from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontend.services.ai_router import AIRouter
from harness.report_writer import write_report

def main():
    r=AIRouter(); health=r.provider_health(); ok='offline_demo' in health and health['offline_demo']['health'] in {'healthy','degraded'}
    write_report('provider_health_smoke', {'ok': ok, 'health': health})
    print('PASS' if ok else 'FAIL'); return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
