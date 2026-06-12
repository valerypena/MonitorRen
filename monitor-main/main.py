import os
import sys
import logging
from controllers.dashboard_controller import DashboardController
from views.dashboard_view import DashboardView

def main():
    # Setup simple console logger for bootstrap phase
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Establish project directories
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(workspace_dir, "config")
    os.makedirs(config_dir, exist_ok=True)
    
    settings_path = os.path.join(config_dir, "settings.json")
    
    logging.info("Initializing REN Enterprise Monitor Controller...")
    # Instantiate Controller
    controller = DashboardController(settings_path)
    
    # Boot background telemetry thread
    logging.info("Starting background network collection loop...")
    controller.start_monitoring()
    
    # Launch GUI View
    logging.info("Launching CustomTkinter GUI...")
    app = DashboardView(controller)
    
    # Start main event loop
    try:
        app.mainloop()
    except KeyboardInterrupt:
        logging.info("Interrupt received, stopping services...")
    finally:
        controller.stop_monitoring()
        logging.info("REN Enterprise Monitor successfully terminated.")

if __name__ == "__main__":
    main()
