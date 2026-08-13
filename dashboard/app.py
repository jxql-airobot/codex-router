"""Desktop UI entry point. Falls back to a text summary without PySide6."""

from __future__ import annotations


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QWidget
    except ImportError:
        from dashboard.widgets import today_summary_widget

        print(today_summary_widget())
        print("PySide6 未安装；已输出文本摘要。")
        return 0

    app = QApplication([])
    window = QWidget()
    window.setWindowTitle("AI Usage Dashboard")
    label = QLabel("AI Usage Dashboard", window)
    label.move(20, 20)
    window.resize(400, 300)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
