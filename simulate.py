import argparse
import time
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

error_graph = {
    "ne": [(-30, 1), (-15, 1), (0, 0), (80, 0)],  # negative error
    "ze": [(-2, 0), (0, 1), (2, 0)],  # zero error (at target)
    "se": [(0, 0), (10, 1), (25, 0)],  # small error
    "me": [(15, 0), (35, 1), (55, 0)],  # medium error
    "le": [(-30, 0), (45, 0), (60, 1), (80, 1)],  # large error
}

error_dot_graph = {
    "if": [(-30, 1), (-15, 1), (-8, 0), (30, 0)],  # improving fast
    "is": [(-12, 0), (-6, 1), (0, 0)],  # improving slow
    "s": [(-3, 0), (0, 1), (3, 0)],  # stable
    "ws": [(0, 0), (6, 1), (12, 0)],  # worsening slow
    "wf": [(-30, 0), (8, 0), (15, 1), (30, 1)],  # worsening fast
}

output_graph = {
    "hi": [(-10, 1), (-8, 1), (-6, 0), (10, 0)],  # strongly increase
    "mi": [(-8, 0), (-6, 1), (-3, 0)],  # moderately increase
    "si": [(-5, 0), (-3, 1), (-1, 0)],  # slightly increase
    "nc": [(-1, 0), (0, 1), (1, 0)],  # no change
    "sl": [(1, 0), (3, 1), (5, 0)],  # slightly lower
    "ml": [(3, 0), (6, 1), (8, 0)],  # moderately lower
    "slo": [(-10, 0), (6, 0), (8, 1), (10, 1)],  # strongly lower
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
    # ne: Trap [(-30,1), (-15,1), (0,0), (80,0)]
    if e <= -15:
        ne = 1
    elif e < 0:
        ne = get_slope((-15, 1), (0, 0)) * e + get_intercept((-15, 1), (0, 0))
    else:
        ne = 0

    # ze: Tri [(-2,0), (0,1), (2,0)]
    if e <= -2:
        ze = 0
    elif e < 0:
        ze = get_slope((-2, 0), (0, 1)) * e + get_intercept((-2, 0), (0, 1))
    elif e < 2:
        ze = get_slope((0, 1), (2, 0)) * e + get_intercept((0, 1), (2, 0))
    else:
        ze = 0

    # se: Tri [(0,0), (10,1), (25,0)]
    if e <= 0:
        se = 0
    elif e < 10:
        se = get_slope((0, 0), (10, 1)) * e + get_intercept((0, 0), (10, 1))
    elif e < 25:
        se = get_slope((10, 1), (25, 0)) * e + get_intercept((10, 1), (25, 0))
    else:
        se = 0

    # me: Tri [(15,0), (35,1), (55,0)]
    if e <= 15:
        me = 0
    elif e < 35:
        me = get_slope((15, 0), (35, 1)) * e + get_intercept((15, 0), (35, 1))
    elif e < 55:
        me = get_slope((35, 1), (55, 0)) * e + get_intercept((35, 1), (55, 0))
    else:
        me = 0

    # le: Trap [(-30,0), (45,0), (60,1), (80,1)]
    if e <= 45:
        le = 0
    elif e < 60:
        le = get_slope((45, 0), (60, 1)) * e + get_intercept((45, 0), (60, 1))
    else:
        le = 1

    return ne, ze, se, me, le

def get_membership_error_dot(ed):
    # if (impf): Trap [(-30,1), (-15,1), (-8,0), (30,0)]
    if ed <= -15:
        impf = 1
    elif ed < -8:
        impf = get_slope((-15, 1), (-8, 0)) * ed + get_intercept((-15, 1), (-8, 0))
    else:
        impf = 0

    # is (imps): Tri [(-12,0), (-6,1), (0,0)]
    if ed <= -12:
        imps = 0
    elif ed < -6:
        imps = get_slope((-12, 0), (-6, 1)) * ed + get_intercept((-12, 0), (-6, 1))
    elif ed < 0:
        imps = get_slope((-6, 1), (0, 0)) * ed + get_intercept((-6, 1), (0, 0))
    else:
        imps = 0

    # s: Tri [(-3,0), (0,1), (3,0)]
    if ed <= -3:
        s = 0
    elif ed < 0:
        s = get_slope((-3, 0), (0, 1)) * ed + get_intercept((-3, 0), (0, 1))
    elif ed < 3:
        s = get_slope((0, 1), (3, 0)) * ed + get_intercept((0, 1), (3, 0))
    else:
        s = 0

    # ws: Tri [(0,0), (6,1), (12,0)]
    if ed <= 0:
        ws = 0
    elif ed < 6:
        ws = get_slope((0, 0), (6, 1)) * ed + get_intercept((0, 0), (6, 1))
    elif ed < 12:
        ws = get_slope((6, 1), (12, 0)) * ed + get_intercept((6, 1), (12, 0))
    else:
        ws = 0

    # wf: Trap [(-30,0), (8,0), (15,1), (30,1)]
    if ed <= 8:
        wf = 0
    elif ed < 15:
        wf = get_slope((8, 0), (15, 1)) * ed + get_intercept((8, 0), (15, 1))
    else:
        wf = 1

    return impf, imps, s, ws, wf

def get_membership_output(x):
    # hi: Trap [(-10,1), (-8,1), (-6,0), (10,0)]
    if x <= -8:
        hi = 1
    elif x < -6:
        hi = get_slope((-8, 1), (-6, 0)) * x + get_intercept((-8, 1), (-6, 0))
    else:
        hi = 0

    # mi: Tri [(-8,0), (-6,1), (-3,0)]
    if x <= -8:
        mi = 0
    elif x < -6:
        mi = get_slope((-8, 0), (-6, 1)) * x + get_intercept((-8, 0), (-6, 1))
    elif x < -3:
        mi = get_slope((-6, 1), (-3, 0)) * x + get_intercept((-6, 1), (-3, 0))
    else:
        mi = 0

    # si: Tri [(-5,0), (-3,1), (-1,0)]
    if x <= -5:
        si = 0
    elif x < -3:
        si = get_slope((-5, 0), (-3, 1)) * x + get_intercept((-5, 0), (-3, 1))
    elif x < -1:
        si = get_slope((-3, 1), (-1, 0)) * x + get_intercept((-3, 1), (-1, 0))
    else:
        si = 0

    # nc: Tri [(-1,0), (0,1), (1,0)]
    if x <= -1:
        nc = 0
    elif x < 0:
        nc = get_slope((-1, 0), (0, 1)) * x + get_intercept((-1, 0), (0, 1))
    elif x < 1:
        nc = get_slope((0, 1), (1, 0)) * x + get_intercept((0, 1), (1, 0))
    else:
        nc = 0

    # sl: Tri [(1,0), (3,1), (5,0)]
    if x <= 1:
        sl = 0
    elif x < 3:
        sl = get_slope((1, 0), (3, 1)) * x + get_intercept((1, 0), (3, 1))
    elif x < 5:
        sl = get_slope((3, 1), (5, 0)) * x + get_intercept((3, 1), (5, 0))
    else:
        sl = 0

    # ml: Tri [(3,0), (6,1), (8,0)]
    if x <= 3:
        ml = 0
    elif x < 6:
        ml = get_slope((3, 0), (6, 1)) * x + get_intercept((3, 0), (6, 1))
    elif x < 8:
        ml = get_slope((6, 1), (8, 0)) * x + get_intercept((6, 1), (8, 0))
    else:
        ml = 0

    # slo: Trap [(-10,0), (6,0), (8,1), (10,1)]
    if x <= 6:
        slo = 0
    elif x < 8:
        slo = get_slope((6, 0), (8, 1)) * x + get_intercept((6, 0), (8, 1))
    else:
        slo = 1

    return hi, mi, si, nc, sl, ml, slo


target_fps = 60
inital_fps = 48
strength = 5

"""
RULES:
1. IF Error is Negative AND Delta is Improving Fast → Output is Strongly Increase (hi)
2. IF Error is Negative AND Delta is Improving Slow → Output is Moderately Increase (mi)
3. IF Error is Negative AND Delta is Stable → Output is Slightly Increase (si)
4. IF Error is Negative AND Delta is Worsening Slowly → Output is No Change (nc)
5. IF Error is Negative AND Delta is Worsening Fast → Output is Slightly Lower (sl)
6. IF Error is Small AND Delta is Improving Fast → Output is Moderately Increase (mi)
7. IF Error is Small AND Delta is Improving Slow → Output is Slightly Increase (si)
8. IF Error is Small AND Delta is Stable → Output is Slightly Lower (sl)
9. IF Error is Small AND Delta is Worsening Slowly → Output is Moderately Lower (ml)
10. IF Error is Small AND Delta is Worsening Fast → Output is Moderately Lower (ml)
11. IF Error is Medium AND Delta is Improving Fast → Output is Slightly Increase (si)
12. IF Error is Medium AND Delta is Improving Slow → Output is Slightly Lower (sl)
13. IF Error is Medium AND Delta is Stable → Output is Moderately Lower (ml)
14. IF Error is Medium AND Delta is Worsening Slowly → Output is Moderately Lower (ml)
15. IF Error is Medium AND Delta is Worsening Fast → Output is Strongly Lower (slo)
16. IF Error is Large AND Delta is Improving Fast → Output is Slightly Lower (sl)
17. IF Error is Large AND Delta is Improving Slow → Output is Moderately Lower (ml)
18. IF Error is Large AND Delta is Stable → Output is Moderately Lower (ml)
19. IF Error is Large AND Delta is Worsening Slowly → Output is Strongly Lower (slo)
20. IF Error is Large AND Delta is Worsening Fast → Output is Strongly Lower (slo)
21. IF Error is Zero AND Delta is Improving Fast → Output is No Change (nc)
22. IF Error is Zero AND Delta is Improving Slow → Output is No Change (nc)
23. IF Error is Zero AND Delta is Stable → Output is No Change (nc)
24. IF Error is Zero AND Delta is Worsening Slow → Output is No Change (nc)
25. IF Error is Zero AND Delta is Worsening Fast → Output is No Change (nc)
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

def print_error_membership(ne, ze, se, me, le):
    print(f"  Error memberships     : ne={ne:.2f}  ze={ze:.2f}  se={se:.2f}  me={me:.2f}  le={le:.2f}")

def print_error_dot_membership(impf, imps, s, ws, wf):
    print(f"  Error Dot memberships : if={impf:.2f}  is={imps:.2f}  s={s:.2f}  ws={ws:.2f}  wf={wf:.2f}")

def print_rules(cap_hi, cap_mi, cap_si, cap_nc, cap_sl, cap_ml, cap_slo):
    print(f"  Rule strengths        : hi={cap_hi:.2f}  mi={cap_mi:.2f}  si={cap_si:.2f}  "
          f"nc={cap_nc:.2f}  sl={cap_sl:.2f}  ml={cap_ml:.2f}  slo={cap_slo:.2f}")

try:
    while True:
        error = args.target - current_fps
        error_dot = error - prev_error

        ne, ze, se, me, le = get_membership_error(error)
        impf, imps, s, ws, wf = get_membership_error_dot(error_dot)

        print(f"\n== Tick {tick} ==")
        print_error_membership(ne, ze, se, me, le)
        print_error_dot_membership(impf, imps, s, ws, wf)

        cap_hi = min(ne, impf)                                                      # rule 1
        cap_mi = max(min(ne, imps), min(se, impf))                                  # rules 2, 6
        cap_si = max(min(ne, s), min(se, imps), min(me, impf))                      # rules 3, 7, 11
        cap_nc = max(
            min(ne, ws),                                                            # rule 4
            min(ze, impf), min(ze, imps), min(ze, s), min(ze, ws), min(ze, wf),     # rules 21-25
        )
        cap_sl = max(min(ne, wf), min(se, s), min(me, imps), min(le, impf))         # rules 5, 8, 12, 16
        cap_ml = max(
            min(se, ws), min(se, wf),
            min(me, s), min(me, ws),
            min(le, imps), min(le, s),
        )                                                                           # rules 9, 10, 13, 14, 17, 18
        cap_slo = max(min(me, wf), min(le, ws), min(le, wf))                        # rules 15, 19, 20

        print_rules(cap_hi, cap_mi, cap_si, cap_nc, cap_sl, cap_ml, cap_slo)

        xs = [i * 0.1 for i in range(-100, 101)]
        hi_ys, mi_ys, si_ys, nc_ys, sl_ys, ml_ys, slo_ys = [], [], [], [], [], [], []

        for x in xs:
            hi_x, mi_x, si_x, nc_x, sl_x, ml_x, slo_x = get_membership_output(x)
            hi_ys.append(min(hi_x, cap_hi))
            mi_ys.append(min(mi_x, cap_mi))
            si_ys.append(min(si_x, cap_si))
            nc_ys.append(min(nc_x, cap_nc))
            sl_ys.append(min(sl_x, cap_sl))
            ml_ys.append(min(ml_x, cap_ml))
            slo_ys.append(min(slo_x, cap_slo))
        max_ys = [max(a, b, c, d, e, f, g)
                  for a, b, c, d, e, f, g
                  in zip(hi_ys, mi_ys, si_ys, nc_ys, sl_ys, ml_ys, slo_ys)]

        sum_xy = sum(x * y for x, y in zip(xs, max_ys))
        sum_y = sum(max_ys)
        z = sum_xy / sum_y if sum_y != 0 else 0.0

        caps = {
            "Strongly increase graphics":   cap_hi,
            "Moderately increase graphics": cap_mi,
            "Slightly increase graphics":   cap_si,
            "No change":                    cap_nc,
            "Slightly lower graphics":      cap_sl,
            "Moderately lower graphics":    cap_ml,
            "Strongly lower graphics":      cap_slo,
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

        prev_fps = current_fps
        # current_fps = max(0, min(100, current_fps + 0.2 * z))
        current_fps = max(0, min(100, current_fps + (strength * (z/100))))
        delta = current_fps - prev_fps
        print(f"  Applied               : Δfps={delta:+.4f}  →  new fps={current_fps:.2f}")

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


