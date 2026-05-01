import argparse
import time
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

error_graph = {
    "ne": [(-30, 1), (-10, 1), (0, 0), (100, 0)],  # negative error
    "se": [(0, 0), (15, 1), (25, 0)],  # small error
    "me": [(20, 0), (40, 1), (55, 0)],  # medium error
    "le": [(-30, 0), (50, 0), (70, 1), (100, 1)],  # large error
}

error_dot_graph = {
    "if": [(-30, 1), (-20, 1), (-10, 0), (30, 0)],  # improving fast
    "is": [(-15, 0), (-5, 1), (0, 0)],  # improving slow
    "s": [(-5, 0), (0, 1), (5, 0)],  # stable
    "ws": [(0, 0), (10, 1), (15, 0)],  # worsening slow
    "wf": [(-30, 0), (10, 0), (20, 1), (30, 1)],  # worsening fast
}

output_graph = {
    "nc": [(0, 1), (15, 1), (20, 0), (100, 0)],  # no change
    "sl": [(15, 0), (30, 1), (40, 0)],  # slightly lower
    "ml": [(35, 0), (50, 1), (65, 0)],  # moderately lower
    "slo": [(0, 0), (60, 0), (80, 1), (100, 1)],  # significantly lower
}

def get_slope(p1, p2):
    """Calculate the slope of a line given two points.

    Args:
        p1: A tuple (x1, y1) for the first point.
        p2: A tuple (x2, y2) for the second point.

    Returns:
        The slope of the line connecting the two points.
    """
    x1, y1 = p1
    x2, y2 = p2
    if x2 - x1 == 0:
        raise ValueError("Cannot calculate slope for vertical line (x1 == x2).")
    return (y2 - y1) / (x2 - x1)

def get_intercept(p1, p2):
    """Calculate the y-intercept of a line given two points.

    Args:
        p1: A tuple (x1, y1) for the first point.
        p2: A tuple (x2, y2) for the second point.
    """
    x1, y1 = p1
    slope = get_slope(p1, p2)
    return y1 - slope * x1

def _extend_points(points, x_min, x_max):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if xs[0] > x_min:
        xs = [x_min] + xs
        ys = [ys[0]] + ys
    if xs[-1] < x_max:
        xs = xs + [x_max]
        ys = ys + [ys[-1]]
    return xs, ys

def draw_fuzzy_graph(ax, fuzzy_dict, title, x_min, x_max, input_value=None, xlabel="Value"):
    ax.clear()
    for label, points in fuzzy_dict.items():
        xs, ys = _extend_points(points, x_min, x_max)
        ax.plot(xs, ys, label=label)
    if input_value is not None:
        ax.axvline(input_value, linestyle="--", color="gray")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Membership")
    ax.set_ylim(-0.05, 1.1)
    ax.set_xlim(x_min, x_max)
    ax.legend()
    ax.grid(True)

def draw_time_series(ax, ticks, fps, errors, target):
    ax.clear()
    ax.plot(ticks, fps, label="FPS", color="tab:blue")
    ax.plot(ticks, errors, label="Error", color="tab:red")
    ax.axhline(target, linestyle="--", color="gray", label=f"Target = {target}")
    ax.axhline(0, linestyle=":", color="lightgray")
    ax.set_title("FPS in Fuzzy Graphics Controller")
    ax.set_xlabel("Time (ticks)")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid(True)

def get_membership_error(e):
    # ne: Trap [(-30,1), (-10,1), (0,0), (100,0)]
    if e <= -10:
        ne = 1
    elif e < 0:
        ne = get_slope((-10, 1), (0, 0)) * e + get_intercept((-10, 1), (0, 0))
    else:
        ne = 0

    # se: Tri [(0,0), (15,1), (25,0)]
    if e <= 0:
        se = 0
    elif e < 15:
        se = get_slope((0, 0), (15, 1)) * e + get_intercept((0, 0), (15, 1))
    elif e < 25:
        se = get_slope((15, 1), (25, 0)) * e + get_intercept((15, 1), (25, 0))
    else:
        se = 0

    # me: Tri [(20,0), (40,1), (55,0)]
    if e <= 20:
        me = 0
    elif e < 40:
        me = get_slope((20, 0), (40, 1)) * e + get_intercept((20, 0), (40, 1))
    elif e < 55:
        me = get_slope((40, 1), (55, 0)) * e + get_intercept((40, 1), (55, 0))
    else:
        me = 0

    # le: Trap [(-30,0), (50,0), (70,1), (100,1)]
    if e <= 50:
        le = 0
    elif e < 70:
        le = get_slope((50, 0), (70, 1)) * e + get_intercept((50, 0), (70, 1))
    else:
        le = 1

    return ne, se, me, le

def get_membership_error_dot(ed):
    # if: Trap [(-30,1), (-20,1), (-10,0), (30,0)]
    if ed <= -20:
        impf = 1
    elif ed < -10:
        impf = get_slope((-20, 1), (-10, 0)) * ed + get_intercept((-20, 1), (-10, 0))
    else:
        impf = 0

    # is: Tri [(-15,0), (-5,1), (0,0)]
    if ed <= -15:
        imps = 0
    elif ed < -5:
        imps = get_slope((-15, 0), (-5, 1)) * ed + get_intercept((-15, 0), (-5, 1))
    elif ed < 0:
        imps = get_slope((-5, 1), (0, 0)) * ed + get_intercept((-5, 1), (0, 0))
    else:
        imps = 0

    # s: Tri [(-5,0), (0,1), (5,0)]
    if ed <= -5:
        s = 0
    elif ed < 0:
        s = get_slope((-5, 0), (0, 1)) * ed + get_intercept((-5, 0), (0, 1))
    elif ed < 5:
        s = get_slope((0, 1), (5, 0)) * ed + get_intercept((0, 1), (5, 0))
    else:
        s = 0

    # ws: Tri [(0,0), (10,1), (15,0)]
    if ed <= 0:
        ws = 0
    elif ed < 10:
        ws = get_slope((0, 0), (10, 1)) * ed + get_intercept((0, 0), (10, 1))
    elif ed < 15:
        ws = get_slope((10, 1), (15, 0)) * ed + get_intercept((10, 1), (15, 0))
    else:
        ws = 0

    # wf: Trap [(-30,0), (10,0), (20,1), (30,1)]
    if ed <= 10:
        wf = 0
    elif ed < 20:
        wf = get_slope((10, 0), (20, 1)) * ed + get_intercept((10, 0), (20, 1))
    else:
        wf = 1

    return impf, imps, s, ws, wf

def get_membership_output(x):
    # nc: Trap [(0,1), (15,1), (20,0), (100,0)]
    if x <= 15:
        nc = 1
    elif x < 20:
        nc = get_slope((15, 1), (20, 0)) * x + get_intercept((15, 1), (20, 0))
    else:
        nc = 0

    # sl: Tri [(15,0), (30,1), (40,0)]
    if x <= 15:
        sl = 0
    elif x < 30:
        sl = get_slope((15, 0), (30, 1)) * x + get_intercept((15, 0), (30, 1))
    elif x < 40:
        sl = get_slope((30, 1), (40, 0)) * x + get_intercept((30, 1), (40, 0))
    else:
        sl = 0

    # ml: Tri [(35,0), (50,1), (65,0)]
    if x <= 35:
        ml = 0
    elif x < 50:
        ml = get_slope((35, 0), (50, 1)) * x + get_intercept((35, 0), (50, 1))
    elif x < 65:
        ml = get_slope((50, 1), (65, 0)) * x + get_intercept((50, 1), (65, 0))
    else:
        ml = 0

    # slo: Trap [(0,0), (60,0), (80,1), (100,1)]
    if x <= 60:
        slo = 0
    elif x < 80:
        slo = get_slope((60, 0), (80, 1)) * x + get_intercept((60, 0), (80, 1))
    else:
        slo = 1

    return nc, sl, ml, slo


target_fps = 90
inital_fps = 28
strength = 3

# RULES
"""
1. IF Error is Large       AND Delta Error is Worsening        THEN Strongly Lower Graphics
2. IF Error is Large       AND Delta Error is Improving Slowly THEN Strongly Lower Graphics
3. IF Error is Large       AND Delta Error is Improving Fast   THEN Lower Graphics            (= Moderately)
4. IF Error is Medium      AND Delta Error is Worsening        THEN Lower Graphics            (= Moderately)
5. IF Error is Medium      AND Delta Error is Improving Slowly THEN Moderately Lower Graphics
6. IF Error is Medium      AND Delta Error is Improving Fast   THEN Slightly Lower Graphics
7. IF Error is Small       AND Delta Error is Improving        THEN No Change
8. IF Error is Small       AND Delta Error is No Change        THEN Stable                    (= No Change)
9. IF Error is Negative                                        THEN No Change

                  if (impf)   is (imps)   s (stable)   ws (slow)   wf (fast)
ne (negative):    nc          nc          nc           nc          nc
se (small):       nc          nc          nc           --          --
me (medium):      sl          ml          --           ml          ml
le (large):       ml          slo         --           slo         slo
"""

parser = argparse.ArgumentParser(description="Fuzzy graphics-quality controller targeting a desired FPS.")
parser.add_argument("--target", type=float, default=float(target_fps),
                    help="Target FPS.")
parser.add_argument("--continuous", action="store_true",
                    help="Run until Ctrl+C instead of auto-stopping when stable.")
args = parser.parse_args()

current_fps = float(inital_fps)
prev_error = 0.0

stable_ticks = 0
tick = 0
tick_history = []
fps_history = []
error_history = []
error_dot_history = []

print("\n-- Initial state --")
print(f"  Target FPS    : {args.target:.2f}")
print(f"  Starting FPS  : {current_fps:.2f}")

def print_error_membership(ne, se, me, le):
    print(f"  Error memberships     : ne={ne:.2f}  se={se:.2f}  me={me:.2f}  le={le:.2f}")

def print_error_dot_membership(impf, imps, s, ws, wf):
    print(f"  Error Dot memberships : if={impf:.2f}  is={imps:.2f}  s={s:.2f}  ws={ws:.2f}  wf={wf:.2f}")

def print_rules(cap_nc, cap_sl, cap_ml, cap_slo):
    print(f"  Rule strengths        : nc={cap_nc:.2f}  sl={cap_sl:.2f}  ml={cap_ml:.2f}  slo={cap_slo:.2f}")

try:
    while True:
        error = args.target - current_fps
        error_dot = error - prev_error

        ne, se, me, le = get_membership_error(error)
        impf, imps, s, ws, wf = get_membership_error_dot(error_dot)

        print(f"\n== Tick {tick} ==")
        print_error_membership(ne, se, me, le)
        print_error_dot_membership(impf, imps, s, ws, wf)

        cap_nc = max(
            min(ne, impf), min(ne, imps), min(ne, s), min(ne, ws), min(ne, wf),
            min(se, impf), min(se, imps), min(se, s),
        )
        cap_sl = min(me, impf)
        cap_ml = max(
            min(me, imps), min(me, ws), min(me, wf),
            min(le, impf),
        )
        cap_slo = max(
            min(le, imps), min(le, ws), min(le, wf),
        )

        print_rules(cap_nc, cap_sl, cap_ml, cap_slo)

        xs = list(range(0, 101))
        nc_ys = []
        sl_ys = []
        ml_ys = []
        slo_ys = []

        for x in xs:
            nc_x, sl_x, ml_x, slo_x = get_membership_output(x)
            nc_ys.append(min(nc_x, cap_nc))
            sl_ys.append(min(sl_x, cap_sl))
            ml_ys.append(min(ml_x, cap_ml))
            slo_ys.append(min(slo_x, cap_slo))
        max_ys = [max(a, b, c, d) for a, b, c, d in zip(nc_ys, sl_ys, ml_ys, slo_ys)]

        sum_xy = sum(x * y for x, y in zip(xs, max_ys))
        sum_y = sum(max_ys)
        z = sum_xy / sum_y if sum_y != 0 else 0.0

        caps = {
            "No change": cap_nc,
            "Slightly lower graphics": cap_sl,
            "Moderately lower graphics": cap_ml,
            "Strongly lower graphics": cap_slo,
        }
        action = max(caps, key=caps.get)

        print(f"  State                 : target={args.target:.2f}  current={current_fps:.2f}  error={error:+.2f}  error_dot={error_dot:+.2f}")
        print(f"  Defuzz output         : z={z:.2f}")
        print(f"  Action                : {action}")

        tick_history.append(tick)
        fps_history.append(current_fps)
        error_history.append(error)
        error_dot_history.append(error_dot)
        tick += 1

        delta = z/100 * strength
        current_fps += delta
        print(f"  Applied               : Δfps={delta:+.4f}  →  new fps={current_fps:.2f}")

        if current_fps > args.target:
            print(f"Ceiling reached: current FPS ({current_fps:.2f}) exceeded target ({args.target:.2f}).")
            break

        if not args.continuous and abs(error) < 0.1:
            stable_ticks += 1
            if stable_ticks >= 10:
                print("Stabilized.")
                break
        else:
            stable_ticks = 0

        prev_error = error
        time.sleep(1.0)
except KeyboardInterrupt:
    print("\nInterrupted.")

final_error = error_history[-1] if error_history else 0
final_error_dot = error_dot_history[-1] if error_dot_history else 0

renderers = [
    lambda ax: draw_fuzzy_graph(ax, error_graph, "Error",
                                x_min=-30, x_max=100,
                                input_value=final_error, xlabel="Error"),
    lambda ax: draw_fuzzy_graph(ax, error_dot_graph, "Error Dot",
                                x_min=-30, x_max=30,
                                input_value=final_error_dot, xlabel="Error Dot"),
    lambda ax: draw_time_series(ax, tick_history, fps_history, error_history, args.target),
]

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
current = [0]

def show_current():
    renderers[current[0]](ax)
    fig.canvas.draw_idle()

def next_plot(event=None):
    current[0] = (current[0] + 1) % len(renderers)
    show_current()

def prev_plot(event=None):
    current[0] = (current[0] - 1) % len(renderers)
    show_current()

ax_prev = plt.axes([0.7, 0.05, 0.1, 0.075])
ax_next = plt.axes([0.81, 0.05, 0.1, 0.075])
btn_prev = Button(ax_prev, "Prev")
btn_next = Button(ax_next, "Next")
btn_prev.on_clicked(prev_plot)
btn_next.on_clicked(next_plot)

def on_key(event):
    if event.key == "left":
        prev_plot()
    elif event.key == "right":
        next_plot()

fig.canvas.mpl_connect("key_press_event", on_key)
show_current()
plt.show()


