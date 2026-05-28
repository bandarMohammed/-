import http.server
import socketserver
import json
import webbrowser
import threading
import os

PORT = 5000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class APIServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static HTML/CSS/JS files from the project directory
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers to enable robust local testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/simulate':
            try:
                # Read POST body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                params = json.loads(post_data)
                
                # Extract parameters
                salary = float(params.get('salary', 0))
                commitments = float(params.get('commitments', 0))
                savings = float(params.get('savings', 0))
                downpayment = float(params.get('downpayment', 0))
                installment = float(params.get('installment', 0))
                duration_years = float(params.get('duration', 1))
                
                # 1. Calculate Debt-to-Income (DTI) Ratio
                total_commitments = commitments + installment
                dti = total_commitments / salary if salary > 0 else 0
                dti_percent = min(round(dti * 100), 100)
                
                # Assess safety indicator
                safety_badge = "آمن ومستقر"
                safety_class = "green"
                if dti > 0.50:
                    safety_badge = "مخاطرة عالية"
                    safety_class = "red"
                    safety_text = f"نسبة الالتزامات الكلية تبلغ <strong style='color: #ef4444;'>{dti_percent}%</strong> من راتبك. هذا يتجاوز الحد الموصى به (45%) وقد يضعك تحت ضغط مالي حاد يؤثر على جودة حياتك اليومية."
                elif dti > 0.35:
                    safety_badge = "حذر / مقيد"
                    safety_class = "orange"
                    safety_text = f"تصل التزاماتك إلى <strong style='color: #f59e0b;'>{dti_percent}%</strong> من الدخل. وضعك مقبول، لكن هامش المناورة المالي لديك ضيق؛ أي التزام مفاجئ قد يخل بميزانيتك."
                else:
                    safety_text = f"وضع مالي ممتاز! تشكل التزاماتك الجديدة مع القديمة <strong style='color: #10b981;'>{dti_percent}%</strong> فقط من الراتب، مما يبقي على فائض مالي مريح للادخار والاستمتاع بمستواك المعيشي."

                # Asset Cost Parameters
                total_months = duration_years * 12
                asset_total_price = downpayment + (installment * total_months)
                living_expenses = salary * 0.30  # Estimated 30% of salary for daily survival

                # --- Scenario 1: Buy Now ---
                monthly_savings_now = salary - commitments - installment - living_expenses
                final_savings_now = max((savings - downpayment) + (monthly_savings_now * 12), 0)
                
                # --- Scenario 2: Wait 6 Months ---
                # Monthly savings capacity during waiting
                wait_monthly_savings = salary - commitments - living_expenses
                accumulated_wait = wait_monthly_savings * 6
                
                # The user adds 80% of accumulated savings to their downpayment
                new_downpayment_wait = downpayment + (accumulated_wait * 0.8)
                new_financed_wait = max(asset_total_price - new_downpayment_wait, 0)
                new_installment_wait = round(new_financed_wait / total_months) if new_financed_wait > 0 else 0
                
                # Savings after buying at month 6 and paying new installment for remaining 6 months
                monthly_savings_after_wait = salary - commitments - new_installment_wait - living_expenses
                final_savings_wait = max((savings + accumulated_wait) - new_downpayment_wait + (monthly_savings_after_wait * 6), 0)
                
                # --- Scenario 3: Optimize Downpayment ---
                # Increase downpayment by 50% immediately (restricted by available savings)
                optimal_downpayment = min(downpayment * 1.5, savings)
                new_financed_opt = max(asset_total_price - optimal_downpayment, 0)
                new_installment_opt = round(new_financed_opt / total_months)
                
                monthly_savings_opt = salary - commitments - new_installment_opt - living_expenses
                final_savings_opt = max((savings - optimal_downpayment) + (monthly_savings_opt * 12), 0)
                
                # Formulate response
                response_data = {
                    "dti_percent": dti_percent,
                    "dti": dti,
                    "safety_badge": safety_badge,
                    "safety_class": safety_class,
                    "safety_text": safety_text,
                    "scenarios": {
                        "now": {
                            "installment": int(installment),
                            "savings": int(final_savings_now)
                        },
                        "wait": {
                            "installment": int(new_installment_wait),
                            "accumulated": int(accumulated_wait),
                            "savings": int(final_savings_wait)
                        },
                        "opt": {
                            "downpayment": int(optimal_downpayment),
                            "installment": int(new_installment_opt),
                            "savings": int(final_savings_opt)
                        }
                    }
                }
                
                # Send HTTP Response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            super().do_POST()

if __name__ == "__main__":
    # Ensure current directory is the script's directory
    os.chdir(DIRECTORY)
    
    # Configure the TCP server to reuse addresses
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), APIServer) as httpd:
        print(f"\n==============================================")
        print(f"🚀 خادم مستشارك المالي الذكي يعمل بنجاح!")
        print(f"🔗 تصفح الموقع على: http://localhost:{PORT}")
        print(f"📦 تم تفعيل الواجهة الخلفية بلغة Python")
        print(f"==============================================\n")
        print("اضغط Ctrl+C في منفذ الأوامر لإيقاف الخادم.")
        
        # Automatically open browser after 1 second
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nتم إيقاف تشغيل الخادم بنجاح.")
            httpd.shutdown()
