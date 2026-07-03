"""
omr_bulk_folder_processor.py

Bulk OMR processing with adaptive filled-bubble detection + absolute fallback
Features:
 - Select folder of images (same template)
 - Create template by selecting ROIs on FIRST image
 - Template scaled to each image
 - Per-row adaptive detection (baseline + delta)
 - Absolute threshold fallback (like the reference)
 - All-4-filled special case handling
 - Light local refinement of bubble bboxes
 - Interactive preview (Prev/Next/Save/Quit)
 - Excel export: two columns per image (S.No (image) | Option (image))
"""

import cv2
import numpy as np
import os
from tkinter import Tk, filedialog
from openpyxl import Workbook

# ---------------- CONFIG ----------------
ROW_VERTICAL_TOLERANCE = 0.02   # fraction of ROI height for grouping rows
MIN_RADIUS_RATIO = 0.01         # Hough min radius (fraction of ROI height)
MAX_RADIUS_RATIO = 0.03         # Hough max radius
MIN_DIST_RATIO = 0.025          # Hough minDist
OPTIONS_PER_QUESTION = 4        # usually 4 (A,B,C,D)
ADAPTIVE_DELTA = 0.18           # per-row margin above baseline for filled decision
ABS_FILL_THRESHOLD = 0.45       # absolute threshold fallback (from your reference)
ALL_FILLED_THRESHOLD = 0.60     # if min(ratios) >= this, mark all as filled
SEARCH_EXPAND_RATIO = 0.6       # local search around bubble for refinement
MIN_BLOB_AREA_RATIO = 0.01      # minimal blob area ratio to consider for refinement
EXCEL_OUTPUT = "omr_bulk_results.xlsx"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
DISPLAY_MAX_W = 1400
DISPLAY_MAX_H = 900
# ----------------------------------------

mouse_state = {"action": None, "x": 0, "y": 0}


def resize_to_fit_screen(img, max_width=DISPLAY_MAX_W, max_height=DISPLAY_MAX_H):
    h, w = img.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def choose_folder():
    root = Tk(); root.withdraw()
    folder = filedialog.askdirectory(title="Select folder containing OMR images")
    root.destroy()
    return folder


def list_images_in_folder(folder):
    files = sorted(os.listdir(folder))
    imgs = [os.path.join(folder, f) for f in files if f.lower().endswith(IMAGE_EXTS)]
    return imgs


def choose_first_image_file(default_path=None):
    root = Tk(); root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select FIRST OMR Image (for template creation)",
        initialdir=os.path.dirname(default_path) if default_path else None,
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff")]
    )
    root.destroy()
    return file_path


def select_multiple_rois_on_image(image):
    display_img, scale = resize_to_fit_screen(image)
    selected_rois = []

    while True:
        temp = display_img.copy()
        for (rx, ry, rw, rh) in selected_rois:
            sx, sy, sw, sh = int(rx * scale), int(ry * scale), int(rw * scale), int(rh * scale)
            cv2.rectangle(temp, (sx, sy), (sx + sw, sy + sh), (0, 165, 255), 2)

        cv2.namedWindow("Select Bubble Regions (ESC when done)", cv2.WINDOW_NORMAL)
        roi_disp = cv2.selectROI("Select Bubble Regions (ESC when done)", temp, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow("Select Bubble Regions (ESC when done)")

        x_disp, y_disp, w_disp, h_disp = roi_disp
        if w_disp == 0 or h_disp == 0:
            break

        x = int(x_disp / scale)
        y = int(y_disp / scale)
        w = int(w_disp / scale)
        h = int(h_disp / scale)

        h_img, w_img = image.shape[:2]
        x = max(0, min(x, w_img - 1))
        y = max(0, min(y, h_img - 1))
        w = max(1, min(w, w_img - x))
        h = max(1, min(h, h_img - y))

        selected_rois.append((x, y, w, h))

    if not selected_rois:
        return None, scale, display_img
    return selected_rois, scale, display_img


def detect_bubbles_in_roi(roi_gray):
    roi_h, roi_w = roi_gray.shape[:2]
    blurred = cv2.GaussianBlur(roi_gray, (7, 7), 1.5)

    min_r = max(1, int(MIN_RADIUS_RATIO * roi_h))
    max_r = max(min_r + 1, int(MAX_RADIUS_RATIO * roi_h))
    min_dist = max(1, int(MIN_DIST_RATIO * roi_h))

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=min_dist,
        param1=80, param2=20, minRadius=min_r, maxRadius=max_r
    )

    if circles is None:
        return []

    circles = np.round(circles[0]).astype(int)

    # deduplicate
    dedup = []
    tol = max(1, int(0.01 * roi_h))
    for cx, cy, r in circles:
        if not any(abs(cx - dx) <= tol and abs(cy - dy) <= tol for dx, dy, _ in dedup):
            dedup.append((cx, cy, r))

    boxes = [(max(0, cx - r), max(0, cy - r), 2 * r, 2 * r) for cx, cy, r in dedup]

    # group by Y center into rows
    boxes_with_cy = [(b, b[1] + b[3] / 2.0) for b in boxes]
    boxes_with_cy.sort(key=lambda t: t[1])

    rows_raw = []
    cur = []
    ref_y = None
    row_tol_px = ROW_VERTICAL_TOLERANCE * roi_h
    for b, cy in boxes_with_cy:
        if ref_y is None or abs(cy - ref_y) <= row_tol_px:
            cur.append(b)
            ref_y = cy if ref_y is None else (ref_y * (len(cur) - 1) + cy) / len(cur)
        else:
            rows_raw.append(cur)
            cur = [b]
            ref_y = cy
    if cur:
        rows_raw.append(cur)

    final_structured = []
    for grp in rows_raw:
        grp_sorted = sorted(grp, key=lambda b: b[0])
        for i in range(0, len(grp_sorted), OPTIONS_PER_QUESTION):
            group = grp_sorted[i:i + OPTIONS_PER_QUESTION]
            if len(group) < OPTIONS_PER_QUESTION:
                continue
            xs = [b[0] for b in group]
            ys = [b[1] for b in group]
            xe = max([b[0] + b[2] for b in group])
            ye = max([b[1] + b[3] for b in group])
            x1 = max(0, min(xs) - 5)
            y1 = max(0, min(ys) - 5)
            w_box = min(roi_w, xe + 5) - x1
            h_box = min(roi_h, ye + 5) - y1

            bubbles_abs = [(int(b[0]), int(b[1]), int(b[2]), int(b[3])) for b in group]

            final_structured.append({
                "row_rect": (int(x1), int(y1), int(w_box), int(h_box)),
                "bubbles": bubbles_abs
            })

    return final_structured


def compute_fill_ratio(roi_gray, bubble):
    x, y, w, h = bubble
    roi_h, roi_w = roi_gray.shape[:2]
    x = max(0, min(x, roi_w - 1))
    y = max(0, min(y, roi_h - 1))
    w = max(1, min(w, roi_w - x))
    h = max(1, min(h, roi_h - y))

    crop = roi_gray[y:y + h, x:x + w]
    if crop.size == 0:
        return 0.0

    margin = int(0.2 * w)
    if margin * 2 >= w or margin * 2 >= h:
        inner = crop
    else:
        inner = crop[margin:h - margin, margin:w - margin]

    if inner.size == 0:
        return 0.0

    _, thresh = cv2.threshold(inner, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    filled = np.count_nonzero(thresh)
    total = thresh.size
    return filled / total if total > 0 else 0.0


def refine_bbox_and_ratio(roi_gray, bubble, search_expand=SEARCH_EXPAND_RATIO, min_blob_area_ratio=MIN_BLOB_AREA_RATIO):
    roi_h, roi_w = roi_gray.shape[:2]
    x, y, w, h = bubble
    x = max(0, min(x, roi_w - 1))
    y = max(0, min(y, roi_h - 1))
    w = max(1, min(w, roi_w - x))
    h = max(1, min(h, roi_h - y))

    expand = int(max(1, search_expand * max(w, h)))
    sx = max(0, x - expand)
    sy = max(0, y - expand)
    ex = min(roi_w, x + w + expand)
    ey = min(roi_h, y + h + expand)
    sw, sh = ex - sx, ey - sy
    if sw <= 0 or sh <= 0:
        return compute_fill_ratio(roi_gray, (x, y, w, h)), (x, y, w, h)

    search_img = roi_gray[sy:sy + sh, sx:sx + sw].copy()
    blur = cv2.GaussianBlur(search_img, (5, 5), 1.0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return compute_fill_ratio(roi_gray, (x, y, w, h)), (x, y, w, h)

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    bubble_area = w * h
    if area < max(5, min_blob_area_ratio * bubble_area):
        return compute_fill_ratio(roi_gray, (x, y, w, h)), (x, y, w, h)

    M = cv2.moments(largest)
    if M["m00"] == 0:
        return compute_fill_ratio(roi_gray, (x, y, w, h)), (x, y, w, h)
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    centroid_x = sx + cx
    centroid_y = sy + cy

    expected_cx = x + w // 2
    expected_cy = y + h // 2
    max_shift = int(0.6 * max(w, h))
    if abs(centroid_x - expected_cx) > max_shift or abs(centroid_y - expected_cy) > max_shift:
        return compute_fill_ratio(roi_gray, (x, y, w, h)), (x, y, w, h)

    adj_x = max(0, min(centroid_x - w // 2, roi_w - w))
    adj_y = max(0, min(centroid_y - h // 2, roi_h - h))
    adj_bbox = (int(adj_x), int(adj_y), int(w), int(h))
    ratio = compute_fill_ratio(roi_gray, adj_bbox)
    return ratio, adj_bbox


def build_template_from_first_image(first_image_path):
    img = cv2.imread(first_image_path)
    if img is None:
        raise RuntimeError("Failed to load first image")

    rois, display_scale, display_img = select_multiple_rois_on_image(img)
    if not rois:
        raise RuntimeError("No ROIs selected for template")

    template = {"template_size": (img.shape[1], img.shape[0]), "rois": []}
    global_q = 1

    for (rx, ry, rw, rh) in rois:
        roi_color = img[ry:ry + rh, rx:rx + rw]
        roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)
        rows = detect_bubbles_in_roi(roi_gray)

        for r in rows:
            r["row_index"] = global_q
            global_q += 1

        template["rois"].append({"roi_rect": (rx, ry, rw, rh), "rows": rows})

    return template, display_scale, display_img


def scale_template_to_image(template, target_img_size):
    tw, th = template["template_size"]
    iw, ih = target_img_size
    sx = iw / tw
    sy = ih / th

    scaled = {"template_size": target_img_size, "rois": []}
    for item in template["rois"]:
        rx, ry, rw, rh = item["roi_rect"]
        s_rx, s_ry, s_rw, s_rh = int(rx * sx), int(ry * sy), int(rw * sx), int(rh * sy)
        scaled_rows = []
        for row in item["rows"]:
            rx_r, ry_r, rw_r, rh_r = row["row_rect"]
            s_rx_r = int(rx_r * sx)
            s_ry_r = int(ry_r * sy)
            s_rw_r = int(rw_r * sx)
            s_rh_r = int(rh_r * sy)
            scaled_bubbles = []
            for bx, by, bw, bh in row["bubbles"]:
                s_bx = int(bx * sx)
                s_by = int(by * sy)
                s_bw = max(1, int(bw * sx))
                s_bh = max(1, int(bh * sy))
                scaled_bubbles.append((s_bx, s_by, s_bw, s_bh))
            scaled_rows.append({
                "row_index": row.get("row_index"),
                "row_rect": (s_rx_r, s_ry_r, s_rw_r, s_rh_r),
                "bubbles": scaled_bubbles
            })
        scaled["rois"].append({"roi_rect": (s_rx, s_ry, s_rw, s_rh), "rows": scaled_rows})
    return scaled


def evaluate_all_images_with_template(template, image_paths):
    images_results = []

    for path in image_paths:
        img = cv2.imread(path)
        if img is None:
            print("Warning: failed to load", path)
            continue

        H, W = img.shape[:2]
        scaled_template = scale_template_to_image(template, (W, H))

        per_question = []
        display_img, display_scale = resize_to_fit_screen(img)
        vis = display_img.copy()
        gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        for roi_item in scaled_template["rois"]:
            rx, ry, rw, rh = roi_item["roi_rect"]
            rx_i = max(0, min(rx, W - 1)); ry_i = max(0, min(ry, H - 1))
            rw_i = max(1, min(rw, W - rx_i)); rh_i = max(1, min(rh, H - ry_i))

            roi_gray = gray_full[ry_i:ry_i + rh_i, rx_i:rx_i + rw_i]

            for row in roi_item["rows"]:
                q_no = row.get("row_index")

                # compute ratios (with refinement) for each bubble
                ratios = []
                refined_bboxes = []
                for b in row["bubbles"]:
                    bx, by, bw, bh = b
                    bx = max(0, min(bx, rw_i - 1))
                    by = max(0, min(by, rh_i - 1))
                    bw = max(1, min(bw, rw_i - bx))
                    bh = max(1, min(bh, rh_i - by))

                    ratio, adj = refine_bbox_and_ratio(roi_gray, (bx, by, bw, bh),
                                                       search_expand=SEARCH_EXPAND_RATIO,
                                                       min_blob_area_ratio=MIN_BLOB_AREA_RATIO)
                    ratios.append(ratio)
                    refined_bboxes.append(adj)

                # handle empty
                if len(ratios) == 0:
                    baseline = 0.0
                    flags = []
                else:
                    # ALL-filled special case
                    if min(ratios) >= ALL_FILLED_THRESHOLD:
                        flags = [True] * len(ratios)
                    else:
                        baseline = float(np.percentile(ratios, 25))
                        # Combined decision:
                        # Mark filled if either (a) ratio >= baseline + ADAPTIVE_DELTA, OR
                        # (b) ratio >= absolute threshold ABS_FILL_THRESHOLD
                        flags = []
                        for r in ratios:
                            flags.append((r >= baseline + ADAPTIVE_DELTA) or (r >= ABS_FILL_THRESHOLD))

                # map flags -> option string
                opts = ['A', 'B', 'C', 'D']
                idxs = [i for i, v in enumerate(flags) if v]
                if len(idxs) == 0:
                    opt_str = "-"
                elif len(idxs) == 1:
                    opt_str = opts[idxs[0]]
                else:
                    opt_str = ",".join(opts[i] for i in idxs)

                per_question.append((q_no, opt_str))

                # visualization
                for i_b, (bx_adj, by_adj, bw_adj, bh_adj) in enumerate(refined_bboxes):
                    color = (0, 0, 255) if flags and flags[i_b] else (0, 255, 0)
                    dbx = int((rx_i + bx_adj) * display_scale)
                    dby = int((ry_i + by_adj) * display_scale)
                    dbw = int(bw_adj * display_scale)
                    dbh = int(bh_adj * display_scale)
                    cv2.rectangle(vis, (dbx, dby), (dbx + dbw, dby + dbh), color, 2)

                # draw row rectangle & label
                rxr, ryr, rwr, rhr = row["row_rect"]
                drx = int((rx_i + rxr) * display_scale)
                dry = int((ry_i + ryr) * display_scale)
                drw = int(rwr * display_scale)
                drh = int(rhr * display_scale)
                cv2.rectangle(vis, (drx, dry), (drx + drw, dry + drh), (255, 0, 0), 2)
                cv2.putText(vis, f"Q{q_no}", (drx + 4, dry + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        images_results.append({
            "image_path": path,
            "image_name": os.path.basename(path),
            "per_question": sorted(per_question, key=lambda x: x[0]),
            "visual": vis
        })

    return images_results


def export_bulk_excel(images_results, output_path=EXCEL_OUTPUT):
    if not images_results:
        print("No results to save.")
        return

    max_q = max(len(item["per_question"]) for item in images_results)

    wb = Workbook()
    ws = wb.active
    ws.title = "OMR Bulk Results"

    header = []
    for item in images_results:
        name = item["image_name"]
        header.append(f"S.No ({name})")
        header.append(f"Option ({name})")
    ws.append(header)

    for i in range(max_q):
        row_vals = []
        for item in images_results:
            if i < len(item["per_question"]):
                q_no, opt = item["per_question"][i]
                row_vals.append(q_no)
                row_vals.append(opt)
            else:
                row_vals.append("")
                row_vals.append("")
        ws.append(row_vals)

    wb.save(output_path)
    print(f"\nExcel saved → {output_path}")


def preview_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_state["action"] = "click"
        mouse_state["x"] = x
        mouse_state["y"] = y


def show_results_preview_interactive(images_results):
    if not images_results:
        print("No images to preview.")
        return None

    idx = 0
    need_redraw = True
    winname = "Bulk OMR Detection Preview - Click Next/Prev or press n/p. 's' saves, 'q' quits."
    cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(winname, preview_mouse)

    while True:
        if need_redraw:
            vis = images_results[idx]["visual"].copy()
            need_redraw = False
        h, w = vis.shape[:2]

        # draw buttons
        btn_h = 40
        margin = 8
        px1, py1 = margin, h - btn_h - margin
        px2, py2 = px1 + 120, py1 + btn_h
        nx1, ny1 = px2 + margin, py1
        nx2, ny2 = nx1 + 120, py1 + btn_h
        sx1, sy1 = nx2 + margin, py1
        sx2, sy2 = sx1 + 140, py1 + btn_h
        qx1, qy1 = sx2 + margin, py1
        qx2, qy2 = qx1 + 100, py1 + btn_h

        cv2.rectangle(vis, (px1, py1), (px2, py2), (200, 200, 200), -1)
        cv2.putText(vis, "Prev (p)", (px1 + 10, py1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.rectangle(vis, (nx1, ny1), (nx2, ny2), (200, 200, 200), -1)
        cv2.putText(vis, "Next (n)", (nx1 + 10, ny1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.rectangle(vis, (sx1, sy1), (sx2, sy2), (80, 200, 100), -1)
        cv2.putText(vis, "Save Excel (s)", (sx1 + 8, sy1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
        cv2.rectangle(vis, (qx1, qy1), (qx2, qy2), (200, 80, 80), -1)
        cv2.putText(vis, "Quit (q)", (qx1 + 12, qy1 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        title = images_results[idx]["image_name"]
        cv2.putText(vis, f"{idx + 1}/{len(images_results)} : {title}", (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow(winname, vis)
        key = cv2.waitKey(20) & 0xFF

        if mouse_state["action"] == "click":
            mx, my = mouse_state["x"], mouse_state["y"]
            mouse_state["action"] = None
            if px1 <= mx <= px2 and py1 <= my <= py2:
                idx = max(0, idx - 1) 
                need_redraw = True
            if nx1 <= mx <= nx2 and ny1 <= my <= ny2:
                idx = min(len(images_results) - 1, idx + 1)
                need_redraw = True
            if sx1 <= mx <= sx2 and sy1 <= my <= sy2:
                return "save"
            if qx1 <= mx <= qx2 and qy1 <= my <= qy2:
                return "quit"

        if key == ord('n'):
            idx = min(len(images_results) - 1, idx + 1)
            need_redraw = True
        if key == ord('p'):
            idx = max(0, idx - 1)
            need_redraw = True
        if key == ord('s'):
            return "save"
        if key == ord('q'):
            return "quit"

    cv2.destroyAllWindows()
    return None


def main():
    print("Select folder containing OMR images (same template for all images).")
    folder = choose_folder()
    if not folder:
        print("No folder selected; exiting."); return

    image_files = list_images_in_folder(folder)
    if not image_files:
        print("No images found in folder; exiting."); return

    print("Select FIRST image to create template (you may choose the first file or another sample).")
    first_img = choose_first_image_file(default_path=image_files[0])
    if not first_img:
        first_img = image_files[0]
        print("No first image selected; using:", first_img)

    print("Building template from:", first_img)
    template, display_scale, display_img = build_template_from_first_image(first_img)

    print("Evaluating images in folder...")
    images_results = evaluate_all_images_with_template(template, image_files)

    action = show_results_preview_interactive(images_results)
    if action == "save":
        export_bulk_excel(images_results)
    else:
        print("Exiting without saving Excel.")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
