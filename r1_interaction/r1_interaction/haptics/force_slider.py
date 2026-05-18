#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from r1_msgs.msg import R1ForceCommands
import tkinter as tk

BG       = "#0f0f17"
BORDER   = "#2a2a40"
TRACK    = "#2d2d44"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
THUMB    = "#c8cfe8"
BTN_GO   = "#16a34a"
BTN_STOP = "#dc2626"

FINGER_COLORS = ["#f59e0b", "#6366f1", "#10b981", "#ef4444"]
MAX_FORCE = 800
THUMB_R   = 8   # thumb radius in pixels
TRACK_H   = 4   # track height in pixels

class _FilledSlider(tk.Canvas):
    def __init__(self, parent, color: str, command=None, **kwargs):
        super().__init__(parent, height=THUMB_R * 2 + 2,
                         bg=BG, highlightthickness=0, **kwargs)
        self._color   = color
        self._command = command
        self._value   = 0

        self.bind("<Configure>",  lambda _: self._redraw())
        self.bind("<Button-1>",   self._on_click)
        self.bind("<B1-Motion>",  self._on_click)

    def _cx(self) -> int:
        """Canvas x-coordinate for current value."""
        w = self.winfo_width()
        r = THUMB_R
        return r + int((self._value / MAX_FORCE) * (w - 2 * r))

    def _x_to_val(self, x: int) -> int:
        w = self.winfo_width()
        r = THUMB_R
        ratio = (x - r) / max(w - 2 * r, 1)
        return int(MAX_FORCE * max(0.0, min(1.0, ratio)))

    def _redraw(self):
        self.delete("all")
        w  = self.winfo_width()
        cy = self.winfo_height() // 2
        r  = THUMB_R
        tx = self._cx()

        # Unfilled track
        self.create_rectangle(r, cy - TRACK_H // 2,
                               w - r, cy + TRACK_H // 2,
                               fill=TRACK, outline="")
        # Filled portion
        if tx > r:
            self.create_rectangle(r, cy - TRACK_H // 2,
                                   tx, cy + TRACK_H // 2,
                                   fill=self._color, outline="")
        # Thumb
        self.create_oval(tx - r, cy - r, tx + r, cy + r,
                         fill=THUMB, outline="")

    def _on_click(self, event):
        self._value = self._x_to_val(event.x)
        self._redraw()
        if self._command:
            self._command(self._value)

    def get(self) -> int:
        return self._value

    def set(self, value: int):
        self._value = int(value)
        self._redraw()

class ForceSliderGUI(Node):
    def __init__(self):
        super().__init__('force_slider_gui')
        self.get_logger().info("Starting Force Slider GUI Node")

        self.declare_parameter('device_id', 50)
        self.declare_parameter('handedness', 'rh')
        device_id = self.get_parameter('device_id').value
        handedness = self.get_parameter('handedness').value
        if handedness not in ('lh', 'rh'):
            self.get_logger().warn(f"Invalid handedness '{handedness}', defaulting to 'rh'")
            handedness = 'rh'
        self.publisher_ = self.create_publisher(
            R1ForceCommands, f'/r1/glove{device_id}/{handedness}/force_commands', 1
        )

        self.values  = [0, 0, 0, 0]
        self.sending = False
        self._build_ui()

    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title("Haptic Force Control")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Header
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(header, text="HAPTIC FORCE CONTROL",
                 font=("Inter", 11, "bold"), fg=MUTED, bg=BG, anchor="w",
                 ).pack(side="left")

        # Finger rows
        self.sliders      = []
        self.value_labels = []

        finger_names = ["Thumb", "Index", "Middle", "Ring"]
        for i, name in enumerate(finger_names):
            self._build_finger_row(i, name, FINGER_COLORS[i])

        # Divider
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(8, 0))

        # Toggle button
        self.toggle_btn = tk.Button(
            self.root,
            text="▶  Start Sending",
            bg=BTN_GO, fg="white",
            font=("Inter", 13, "bold"),
            relief="flat", bd=0, cursor="hand2",
            activebackground="#15803d", activeforeground="white",
            command=self.toggle_sending,
        )
        self.toggle_btn.pack(fill="x", padx=24, pady=(14, 6), ipady=10)

        # Status bar
        self.status_label = tk.Label(
            self.root, text="idle  ·  [0, 0, 0, 0]",
            font=("Courier", 10), fg=MUTED, bg=BG,
        )
        self.status_label.pack(pady=(0, 16))

    def _build_finger_row(self, idx: int, name: str, color: str):
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=24, pady=6)

        # Colored dot
        dot = tk.Canvas(row, width=10, height=10, bg=BG, highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=color, outline="")
        dot.pack(side="left", pady=4)

        # Finger name
        tk.Label(row, text=name, width=7, anchor="w",
                 font=("Inter", 12), fg=TEXT, bg=BG,
                 ).pack(side="left", padx=(6, 0))

        # Single-line filled slider
        slider = _FilledSlider(row, color=color,
                               command=lambda val, i=idx: self._on_slider(i, val))
        slider.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.sliders.append(slider)

        # Value badge
        val_lbl = tk.Label(row, text="0", width=5, anchor="e",
                           font=("Courier", 11, "bold"), fg=color, bg=BG)
        val_lbl.pack(side="left", padx=(10, 0))
        self.value_labels.append(val_lbl)

    def _on_slider(self, idx: int, val: int):
        self.values[idx] = val
        self.value_labels[idx].config(text=str(val))
        self._refresh_status()

    def _refresh_status(self):
        prefix = "sending" if self.sending else "idle"
        self.status_label.config(text=f"{prefix}  ·  {self.values}")

    def publish_forces(self):
        msg = R1ForceCommands()
        msg.force_values = self.values
        self.publisher_.publish(msg)

    def toggle_sending(self):
        self.sending = not self.sending
        if self.sending:
            self.toggle_btn.config(text="■  Stop Sending",
                                   bg=BTN_STOP, activebackground="#b91c1c")
            self._schedule_publish()
        else:
            self.toggle_btn.config(text="▶  Start Sending",
                                   bg=BTN_GO, activebackground="#15803d")
        self._refresh_status()

    def _schedule_publish(self):
        if self.sending:
            self.publish_forces()
            self.root.after(50, self._schedule_publish)

    def run(self):
        self.root.mainloop()

def main(args=None):
    rclpy.init(args=args)
    node = ForceSliderGUI()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()