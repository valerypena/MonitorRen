import threading
from typing import Dict, Any, Callable
from models.diagnostics_model import DiagnosticsModel
from system_diagnostic import SystemDiagnostic

class DiagnosticsController:
    def __init__(self, model: DiagnosticsModel, settings: Dict[str, Any]):
        self.model = model
        self.settings = settings
        self.diagnostic_service = SystemDiagnostic(settings)
        
    def run_diagnostics(self, current_payload: Dict[str, Any], on_progress_update: Callable[[float], None], on_result_added: Callable[[Dict[str, Any]], None], on_complete: Callable[[str], None]) -> None:
        """
        Runs diagnostics in a background thread to keep Tkinter GUI responsive.
        """
        if self.model.is_running:
            return
            
        self.model.reset()
        
        def _thread_target():
            def _progress_callback(prog: float):
                self.model.update_progress(prog)
                # Call view callback on main thread
                on_progress_update(prog)
                
            # Run checks
            raw_results, report_path, final_state = self.diagnostic_service.run_all_checks(
                current_payload, 
                _progress_callback
            )
            
            # Fill model
            for r in raw_results:
                self.model.add_result(r["name"], r["status"], r["value"], r["notes"])
                on_result_added(r)
                
            self.model.last_report_path = report_path
            self.model.is_running = False
            
            # Invoke complete callback
            on_complete(report_path)
            
        t = threading.Thread(target=_thread_target, daemon=True)
        t.start()
