from killswitch import app
from looper import run_loop
import state

if __name__ == "__main__":
    print("================================")
    print("PHANTOM SEATS VPS")
    print("================================")
    print("Kill switch: http://0.0.0.0:5000")
    print("================================")
    
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
