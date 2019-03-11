import time
from selenium import webdriver
import http.client
import urllib
import requests
import ruamel.yaml as yaml

configfile_name = 'config.yml'

# Check if there is already a configuration file
#if not configfile_name.is_file():
    # Create the configuration file as it doesn't exist yet
#cfg_file = open(configfile_name, 'w+')

with open(configfile_name, 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.Loader)

name = cfg['applicant']['name']
phone_number = cfg['applicant']['phone_number']
email_address = cfg['applicant']['email_address']
request_appointment = cfg['settings']['reqeust_appointment']
time_between_checks = cfg['settings']['time_between_checks']
default_time_between_checks = 90
pushover_app_token = cfg['settings']['pushover_app_token']
pushover_user_api = cfg['settings']['pushover_user_api']

class AppointmentChecker:
    def __init__(self):
        # Initialize chrome library and store any variables inside the class
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument("--test-type")
        self.options.add_argument("--headless")
        self.prefs = {"profile.managed_default_content_settings.images": 2}
        self.options.add_experimental_option("prefs", self.prefs)

    def is_appointment_available(self):
        # Simulates the entire workflow of a user checking for an appointment opening
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_window_size(1000, 1000)
        self.driver.get(
            'https://veribook.com/ew.jsp?cpUserId=268858&cpAlias=RsSdEFrhMz465&mobileSupport=true#hId=1')
        time.sleep(15)
        #html_source = self.driver.page_source
        try:
            dropdown = self.driver.find_element_by_xpath(
                '//*[@id="contentNode"]/div/div/div[2]/div/div/div/div[2]/div[6]/div/form/div[2]/div[2]/div/select')
            dropdown.click()
            time.sleep(1)

            dropdown_option2= self.driver.find_element_by_xpath(
                '//*[@id="contentNode"]/div/div/div[2]/div/div/div/div[2]/div[6]/div/form/div[2]/div[2]/div/select/option[2]')
            dropdown_option2.click()
            time.sleep(1)

            message = self.driver.find_element_by_xpath(
                '//*[@id="amobius_ui_widget_Dialog_0"]/div[2]/span[2]/span[1]')
            message_text = message.text
            print(message_text)

            if "no appointments are available" in message_text:
                return False
            else:
                self.driver.save_screenshot('screenshot.png')
                return True
        finally:
            self.driver.close()

def send_message(message):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": pushover_app_token,
        "user": pushover_user_api,
        "message": message,
    }), {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()

def send_image(image):
    r = requests.post("https://api.pushover.net/1/messages.json", data = {
        "token": pushover_app_token,
        "user": pushover_user_api,
        "message": "Website Screenshot"
        },
    files = {
        "attachment": (image, open(image, "rb"), "image/png")
    })
    print(r.text)

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def main():
    global name
    global phone_number
    global email_address
    global time_between_checks
    global default_time_between_checks
    global pushover_app_token
    global pushover_user_api
    notify = False

    if request_appointment == None:
        if query_yes_no("Would you like to accept the next appointment that is available? (Type y or n)", default="no"):
            if name == None:
                name = input("What is your name?\n")
            if phone_number == None:
                phone_number = input("What is your phone number?\n")
            if email_address == None:
                email_address = input("What is your email address?\n")
            print("Booking the next available appointment I find as\n" + name + "\n" + phone_number + "\n" + email_address + "\n")
        else:
            print("Searching for appointments, not booking")

    if query_yes_no("Would you like to be notified via Pushover (pushover.net)? (Type y or n)", default="no"):
        if pushover_app_token == None:
            print("Pushover Application API Token not set in config.yml. Please add it and try again.")
            notify = False
        elif pushover_user_api == None:
            print("Pushover User API Token not set in config.yml. Please add it and try again.")
            notify = False
        else:
            notify = True
    else:
        notify = False
    
    if notify:
        print("Starting to check for appointments. You will be notified via Pushover if an appointment is found.")
    else:
        print("Starting to check for appointments. You will NOT be notified of found appointments.")
    #send_message("Started checking for appointments")
    if time_between_checks == None or not isinstance(time_between_checks, int):
        time_between_checks = default_time_between_checks
        print("Using the default time between checks of " + str(default_time_between_checks) + " seconds.")
    checker = AppointmentChecker()
    consecutive_errors = 0
    number_of_checks = 0
    while True:
        number_of_checks = number_of_checks + 1
        try:
            if checker.is_appointment_available():
                print("Passport appointment available!")
                if notify == True:
                    send_message("Passport appointment available!\nhttps://veribook.com/ew.jsp?cpUserId=268858&cpAlias=RsSdEFrhMz465&mobileSupport=true#hId=1")
                    send_image('screenshot.png')
                break
            else:
                if notify == True:
                    send_message("Not available")
                print("Not available :(")
            consecutive_errors = 0
        except:
            consecutive_errors = consecutive_errors + 1
            if consecutive_errors > 5:
                if notify == True:
                    send_message("I'm seeing a lot of errors")
                break
        finally:
            print("Checked " + str(number_of_checks) + " time(s).")
            print("Trying again in " + str(time_between_checks) + " seconds.")
            time.sleep(time_between_checks)
    print("Bye")

main()
