import requests
import smtplib
from email.mime.text import MimeText
import time
import platform

class PhoneLocator:
    def _init_(self):
        self.phone_number = ""  # Add phone number
        self.email_credentials = {
            "email": "your_email@gmail.com",
            "password": "your_app_password",
            "to_email": "receiver@gmail.com"
        }
    
    def get_location_info(self):
        """Get approximate location using IP address"""
        try:
            response = requests.get('http://ipinfo.io')
            data = response.json()
            return {
                'ip': data.get('ip', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'loc': data.get('loc', 'Unknown')  # Latitude,Longitude
            }
        except:
            return {"error": "Could not fetch location"}
    
    def send_location_email(self, location_info):
        """Send location via email"""
        try:
            subject = "LOST PHONE LOCATION ALERT"
            body = f"""
            LOST PHONE LOCATION INFORMATION:
            
            IP Address: {location_info.get('ip', 'Unknown')}
            Location: {location_info.get('city', 'Unknown')}, {location_info.get('region', 'Unknown')}
            Country: {location_info.get('country', 'Unknown')}
            Coordinates: {location_info.get('loc', 'Unknown')}
            
            Time: {time.ctime()}
            """
            
            msg = MimeText(body)
            msg['Subject'] = subject
            msg['From'] = self.email_credentials['email']
            msg['To'] = self.email_credentials['to_email']
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_credentials['email'], 
                           self.email_credentials['password'])
                server.send_message(msg)
            
            print("Location email sent successfully!")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def trigger_alarm(self):
        """Simulate making the phone ring/locate"""
        print("🔊 Phone alarm triggered! Follow the sound!")
        # This would need mobile app integration for actual implementation
    
    def run_locator(self):
        """Main function to locate phone"""
        print("🔄 Attempting to locate phone...")
        
        # Get location
        location = self.get_location_info()
        print(f"📍 Approximate Location: {location}")
        
        # Send email with location
        self.send_location_email(location)
        
        # Trigger alarm
        self.trigger_alarm()

# Usage
if _name_ == "_main_":
    locator = PhoneLocator()
    locator.run_locator()