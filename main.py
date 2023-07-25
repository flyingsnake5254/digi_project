'''
LCD :
    SDA:12
    SCL:17

LED LINE:
    DIG:0
    
SERVO:
    PIN:16

led:
    PIN:20
    PIN:21
button:
    PIN:4
'''

from machine import *
from utime import *
from pico_i2c_lcd import *
from mneopixel import *
import network
import urequests
import random


class Servo:
    def __init__(self, pin):
        self.servo = PWM(Pin(pin))
        self.servo.freq(50)
        self.reset()
    
    def rotate(self, degree):
        self.degree = degree
        dc = (0.12 - 0.025) / 180 * degree + 0.025
        self.servo.duty_u16(int(65535 * dc))
        
    def reset(self):
        self.rotate(180)
        
    def close(self):
        self.servo.deinit()

led = Pin(20, Pin.OUT)
led2 = Pin(21, Pin.OUT)
system_led = Pin("LED", Pin.OUT)
btn1 = Pin(4, Pin.IN, Pin.PULL_DOWN)
btn2 = Pin(14, Pin.IN, Pin.PULL_DOWN)
servo = Servo(16)

#LCD INIT
I2C_ADDR = 39
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
i2c = I2C(0, sda=Pin(12), scl=Pin(17))
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

#led line
numpix = 8
state_machine = 0
led_line_pin = 0
led_line = Neopixel(numpix, 0, led_line_pin, 'GRB')

red = (255, 0, 0)
orange = (150, 20, 0)
yellow = (255, 200, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
indigo = (75, 0, 130)
violet = (255, 10, 50)
brown = (240, 0, 200)
black = (0,0,0)

pm25_bright_dark = [0, 1, 1, 1, 2, 2, 2]
pm25_color_dark = [
    (0, 0, 0),
    (0, 255, 0),
    (255, 200, 0),
    (200, 50, 0),
    (255, 0, 10),
    (100, 10, 100),
    (50, 0, 255)
]
pm25_bright_light = [0, 50, 50, 50, 50, 50, 100]
pm25_color_light = [
    (0, 0, 0),
    (0, 255, 0),
    (255, 200, 0),
    (200, 50, 0),
    (255, 0, 0),
    (100, 20, 100),
    (10, 0, 255)
]

led_line.clear()

for i in range(1, 7):
    led_line.set_pixel(i, pm25_color_dark[i], pm25_bright_dark[i])
led_line.show()

# function list
function_list = ['show pm2.5 value', '1A2B game']
now_function = 0

def reset_home_page():
    global now_function
    
    lcd.hide_cursor()
    lcd.clear()
    lcd.move_to(0,0)
    lcd.putstr('select function')
    lcd.move_to(0,1)
    now_function = 0
    lcd.putstr(function_list[now_function])
    
    # led line reset
    led_line.clear()
    led_line.show()
    led.off()
    led2.off()
    
    # servo reset
    servo.reset()
    
def pm25_level(v):
    if v == 'no data':
        return -1
    else:
        value = eval(v)
        if value <= 15:
            return 1
        elif value > 15 and value <= 35:
            return 2
        elif value > 35 and value <= 54:
            return 3
        elif value >54 and value <= 70:
            return 4
        elif value > 70 and value < 85:
            return 5
        else:
            return 6


def page_pm25():
    # led line reset
    led_line.clear()

    for i in range(1, 7):
        led_line.set_pixel(i, pm25_color_dark[i], pm25_bright_dark[i])
    led_line.show()
    # wifi
    SSID = 'Pixel_6123'
    PASSWORD = '99999999'
     
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    dots = 2
    lcd.clear()
    lcd.move_to(0,0)
    lcd.putstr('wairing to connect'+'.'*dots)
    while not (wlan.isconnected() or wlan.status() == network.STAT_GOT_IP):
        if dots == 5:
            lcd.move_to(2,1)
            lcd.putstr('   ')
            lcd.move_to(2,1)
            dots = 2
        lcd.move_to(dots,1)
        lcd.putstr('.')
        dots += 1
        utime.sleep(1)

    lcd.clear()
    lcd.move_to(0,0)
    lcd.putstr('connected')
    sleep(2)

    url = 'https://data.epa.gov.tw/api/v2/aqx_p_02?api_key=e8dd42e6-9b8b-43f8-991e-b3dee723a52d&limit=1000&sort=datacreationdate%20desc&format=JSON'
    res = urequests.get(url=url)
    data = res.json()
    api_data = {}
    for key, value in data.items():
        api_data.update({key: value})      
    res.close()


    countys_en = {
        "雲林縣": "Yunlin",
        "屏東縣": "Pingtung",
        "苗栗縣": "Miaoli",
        "新北市": "New Taipei City",
        "高雄市": "Kaohsiung City",
        "嘉義市": "Chiayi City",
        "臺北市": "Taipei City",
        "南投縣": "Nantou",
        "臺南市": "Tainan City",
        "花蓮縣": "Hualien",
        "新竹市": "Hsinchu City",
        "基隆市": "Keelung City",
        "新竹縣": "Hsinchu",
        "臺中市": "Taichung City",
        "彰化縣": "Changhua",
        "宜蘭縣": "Yilan",
        "桃園市": "Taoyuan City",
        "澎湖縣": "Penghu",
        "臺東縣": "Taitung",
        "連江縣": "Lienchiang",
        "金門縣": "Kinmen",
        "嘉義縣": "Chiayi"
    }

    pm25 = {}
    for i in api_data['records']:
        if i['pm25'] == '':
            pm25.update({countys_en[i['county']]: 'no data'})
        else:
            pm25.update({countys_en[i['county']]: i['pm25']})

    counties = []
    for key, value in pm25.items():
        counties.append(key)

    lcd.clear()
    lcd.move_to(0,0)
    lcd.putstr('select county')
    lcd.move_to(0,1)
    lcd.putstr(counties[0])
    now_county = 0
    show_pm25_data = False


    is_press = False
    exe_page = True
    while exe_page:
        if show_pm25_data:
            lcd.clear()
            lcd.move_to(0,0)
            lcd.putstr(counties[now_county])
            lcd.move_to(0,1)
            lcd.putstr('pm2.5 :' + pm25[counties[now_county]])
            level = pm25_level(pm25[counties[now_county]])
            servo.rotate(210 - level * 30)
            for i in range(1, 7):
                if i == level:
                    led_line.set_pixel(i, pm25_color_light[i], pm25_bright_light[i])
                else:
                    led_line.set_pixel(i, pm25_color_dark[i], pm25_bright_dark[i])
            led_line.show()
            
            while True:
                if btn2.value() == 1:
                    show_pm25_data = False
                    servo.reset()
                    lcd.clear()
                    lcd.move_to(0,0)
                    lcd.putstr('select county')
                    lcd.move_to(0,1)
                    lcd.putstr(counties[0])
                    now_county = 0
                    for i in range(1, 7):
                        led_line.set_pixel(i, pm25_color_dark[i], pm25_bright_dark[i])
                    led_line.show()
                    break
        else:
            if btn1.value() == 1:
                now_county += 1
                if now_county == len(counties):
                    now_county = 0
                lcd.move_to(0,1)
                lcd.putstr(' '*16)
                lcd.move_to(0,1)
                lcd.putstr(counties[now_county])
                
            # btn2 is short or long click
            if btn2.value() == 1 and is_press == False:
                is_press = True
                start_press_time = time.ticks_ms()
            elif btn2.value() == 0 and is_press:
                end_press_time = time.ticks_ms()
                if ticks_diff(end_press_time, start_press_time) > 500:    
                    exe_page = False
                    reset_home_page()
                else:
                    show_pm25_data = True
                is_press = False

                
def page_1a2b():
    # set lcd
    lcd.show_cursor()
    lcd.clear()
    lcd.move_to(0,0)
    lcd.putstr('hint:0A0B')
    lcd.move_to(0,1)
    lcd.putstr('0000')
    lcd.move_to(0,1)
    ans = [str(random.randint(0, 9)), str(random.randint(0, 9)), str(random.randint(0, 9)), str(random.randint(0, 9))]
    exe_game = True
    btn1_is_press = False
    btn2_is_press = False
    set_number = False
    now_cursor = 0
    now_ans = ['0','0','0','0']
    if_again = False
    print('ans : ',ans)
    while exe_game:
        # small led
        if set_number:
            led.on()
            led2.off()
        else:
            led.off()
            led2.on()
        # btn1 short or long click
        if btn1.value() == 1 and btn1_is_press == False:
            btn1_is_press = True
            btn1_start_press_time = time.ticks_ms()
        elif btn1.value() == 0 and btn1_is_press:
            btn1_end_press_time = time.ticks_ms()
            if ticks_diff(btn1_end_press_time, btn1_start_press_time) > 500:
                #long click
                if set_number == False:
                    # check ?a?b
                    a_num = 0
                    b_num = 0

                    for i in range(4):
                        if ans[i] == now_ans[i]:
                            a_num += 1

                    t = ans.copy()
                    for i in range(4):
                        if now_ans[i] in t:
                            b_num += 1
                            t.pop(t.index(now_ans[i]))

                    b_num -= a_num
                    lcd.move_to(5,0)
                    lcd.putstr(str(a_num))
                    lcd.move_to(7,0)
                    lcd.putstr(str(b_num))
                    
                    # 4A
                    if a_num == 4:
                        # led
                        led_line.clear()
                        color_1a2b = [red, orange, yellow, green, blue, indigo, violet, brown]
                        for i in range(3):
                            for j in range(8):
                                for k in range(8):
                                    if j == k:
                                        led_line.set_pixel(k, color_1a2b[k], 30)
                                    else:
                                        led_line.set_pixel(k, black, 0)
                                led_line.show()
                                sleep(0.1)
                        led_line.clear()
                        led_line.show()

                        lcd.move_to(12,0)
                        lcd.putstr('win!')
                        lcd.move_to(0,1)
                        lcd.putstr(' '*16)
                        lcd.move_to(0,1)
                        lcd.putstr('again? yes no')
                        lcd.move_to(7,1)
                        now_cursor = 7
                        if_again = True
                    else:
                        # led
                        led_line.clear()
                        for i in range(3):
                            for j in range(8):
                                led_line.set_pixel(j, red, 30)
                            led_line.show()
                            sleep(0.15)
                            for j in range(8):
                                led_line.set_pixel(j, black, 0)
                            led_line.show()
                            sleep(0.15)
                        led_line.clear()
                        led_line.show()
                        now_cursor = 0
                        lcd.move_to(now_cursor,1)

                    
            elif ticks_diff(btn1_end_press_time, btn1_start_press_time) > 100:
                #short click
                if if_again:
                    if now_cursor == 7:
                        now_cursor = 11
                        lcd.move_to(now_cursor,1)
                    else:
                        now_cursor = 7
                        lcd.move_to(now_cursor,1)
                else:
                    if set_number == False:
                        now_cursor += 1
                        if now_cursor == 4:
                            now_cursor = 0
                        lcd.move_to(now_cursor,1)
                    elif set_number:
                        temp_v = eval(now_ans[now_cursor])
                        temp_v += 1
                        if temp_v == 10:
                            temp_v = 0
                        lcd.move_to(now_cursor,1)
                        lcd.putstr(str(temp_v))
                        lcd.move_to(now_cursor,1)
                        now_ans[now_cursor] = str(temp_v)
            btn1_is_press = False
            
        # btn2 short or long click    
        if btn2.value() == 1 and btn2_is_press == False:
            btn2_is_press = True
            btn2_start_press_time = time.ticks_ms()
        elif btn2.value() == 0 and btn2_is_press:
            btn2_end_press_time = time.ticks_ms()
            if ticks_diff(btn2_end_press_time, btn2_start_press_time) > 500:
                #long click
                if set_number == False:
                    exe_game = False
                    reset_home_page()
            else:
                #short click
                if if_again:
                    if now_cursor == 7:
                        # again
                        lcd.show_cursor()
                        lcd.clear()
                        lcd.move_to(0,0)
                        lcd.putstr('hint:0A0B')
                        lcd.move_to(0,1)
                        lcd.putstr('0000')
                        lcd.move_to(0,1)
                        ans = [str(random.randint(0, 9)), str(random.randint(0, 9)), str(random.randint(0, 9)), str(random.randint(0, 9))]
                        exe_game = True
                        btn1_is_press = False
                        btn2_is_press = False
                        set_number = False
                        now_cursor = 0
                        now_ans = ['0','0','0','0']
                        if_again = False
                        print('ans : ',ans)
                    else:
                        exe_game = False
                        reset_home_page()
                        
                else:
                    if set_number == False:
                        set_number = True
                    elif set_number:
                        set_number = False
            btn2_is_press = False

def page_home():
    global now_function

    # show home page
    reset_home_page()

    while True:
        if btn1.value() == 1:
            now_function += 1
            if now_function == len(function_list):
                now_function = 0
            lcd.move_to(0,1)
            lcd.putstr(' ' * 16)
            lcd.move_to(0,1)
            lcd.putstr(function_list[now_function])
        if btn2.value() == 1:
            if now_function == 0:
                # pm2.5
                page_pm25()
            elif now_function == 1:
                # 1A2B game
                page_1a2b()

page_home()


            
            
        








