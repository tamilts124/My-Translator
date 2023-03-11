import pyscreenshot, cv2, sys, os
import requests, googletrans
from tkinter import *
from tkinter import messagebox
from pynput import keyboard
from threading import Thread
import numpy as np

langs =googletrans.LANGUAGES
short_langs, long_langs = list(langs.keys()), list(langs.values())
inwindow, oldinfo =False, []

extractseconds =60

def release_detection(key):
    if str(key)=="Key.ctrl_r":
        if keystokes and not keystokes[0]: keystokes.clear()
        keystokes.append(True)
    elif str(key)=="Key.ctrl_l":
        if keystokes and keystokes[0]: keystokes.clear()
        keystokes.append(False)
    else: keystokes.clear()
    if len(keystokes)>=3: klistener.stop()

def mouse_crop(event, x, y, flags, param):
    # grab references to the global variables
    global x_start, y_start, x_end, y_end, cropping, cropped

    if event == cv2.EVENT_LBUTTONDOWN:
        x_start, y_start, x_end, y_end = x, y, x, y
        cropping = True
    # Mouse is Moving
    elif event == cv2.EVENT_MOUSEMOVE:
        if cropping == True:
            x_end, y_end = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates
        x_end, y_end = x, y
        cropping = False # cropping is finished
        if x_start>x_end or y_start>y_end:
            x_start, x_end, y_start, y_end =x_end, x_start, y_end, y_start
        refPoint = [(x_start, y_start), (x_end, y_end)]
        if len(refPoint) == 2: #when two points were found
            cropimage = image[refPoint[0][1]:refPoint[1][1], refPoint[0][0]:refPoint[1][0]]
            cropped =True
            if cropimage.any():
                image_bytes = cv2.imencode('.jpg', cropimage)[1].tobytes()
                Thread(target=imageTotranslate, args=[image_bytes, extractseconds, 5]).start()

def imageTotranslate(image_bytes, timeout, attempt):
    global inwindow
    text =imgdataTotextdata(image_bytes, timeout, attempt)
    if inwindow:
        oldinfo[0].focus_set()
        oldinfo[1].delete('1.0', 'end')
        oldinfo[1].insert('1.0', text)
        return
    window =Tk()
    inwindow =True
    window.config(padx=10, pady=20)
    window.title('Translator')
    textv =Text(window, padx=10, pady=20, undo=True, wrap='none')
    textv.insert('1.0', text); textv.grid(row=1)
    frame1 =Frame(window, pady=10)
    detect =Button(frame1, text='Detect Language', padx=10, pady=2, command=lambda:detect_lang(textv.get('1.0', 'end')))
    label1 =Label(frame1, text='Source Language: ', padx=5, pady=2)
    source =Listbox(frame1, height=1, exportselection=0)
    label2 =Label(frame1, text='Destination Language: ', padx=5, pady=2)
    destination =Listbox(frame1, height=1, exportselection=0)
    for i in long_langs:
        source.insert('end', i)
        destination.insert('end', i)
    source.insert(0, 'auto')
    detect.grid(row=1, column=1); label1.grid(row=1, column=2)
    source.grid(row=1, column=3); label2.grid(row=1, column=4)
    destination.grid(row=1, column=5); frame1.grid(row=2)
    source.selection_set(0)
    destination.selection_set(0)
    frame2 =Frame(window, pady=10)
    exteditor =BooleanVar()
    checkbutton =Checkbutton(frame2, variable=exteditor, text='Open with system Editor')
    buttonv =Button(frame2, padx=10, pady=5, text='Translate', command=lambda:translator(textv.get('1.0', 'end'),
        [short_langs[long_langs.index(source.get('active'))] if not source.get('active')=='auto' else 'auto'][0],
        short_langs[long_langs.index(destination.get('active'))], exteditor.get()))
    checkbutton.grid(row=1, column=1)
    buttonv.grid(row=1, column=2); window.focus_set()
    frame2.grid(row=3)
    window.protocol('WM_DELETE_WINDOW', lambda:window_destroy(window))
    oldinfo.append(window); oldinfo.append(textv)
    window.mainloop()

def imgdataTotextdata(imgdata, timeout, attempt):
    while attempt:
        attempt-=1
        try:
            response =requests.post(url='https://blackboxapp.co/getsingleimage',
            files={'photo':('62d4ffe508808700315c9cd0.jpg', imgdata)}, timeout=timeout)
        except requests.exceptions.ReadTimeout: break
        text =response.json()
        if text=='Error': continue
        return text['text']
    return '' 

def translator(text, src, dest, openexteditor):
    text =translate(text, src, dest)
    if not text.strip(' \t\n'): messagebox.showwarning('Text Error', 'No Letter In Editor'); return
    if openexteditor: openExternalEditor(text); return
    window =Tk()
    window.title('Translation')
    textv =Text(window, padx=10, pady=20, undo=True, wrap='none')
    textv.insert('1.0', text)
    textv.pack()
    window.focus_set()
    window.mainloop()

def translate(text, src='auto', dest='en'):
    translator =googletrans.Translator()
    if src.lower()=='auto':
        result =translator.detect(text)
        result =translator.translate(text, src=result.lang, dest=dest)
    else: result =translator.translate(text, src=src, dest=dest)
    return result.text

def detect_lang(text):
    if not text.strip(' \t\n'): messagebox.showwarning('Text Error', 'No Letter In Editor'); return
    translator =googletrans.Translator()
    result =translator.detect(text)
    messagebox.showinfo('Information', 'Language: '+langs.get(result.lang)+'\nConfident: '+str(result.confidence))
    
def window_destroy(window):
    global inwindow
    inwindow =False
    oldinfo.clear()
    window.destroy()

def openExternalEditor(text):
    with open('temp.txt', 'wt') as txt:
        if txt.writable: txt.write(text)
        else: messagebox.showerror("Can't Write", 'Not have a Permission to Write'); return
    if sys.platform.lower()[:3]=='win': os.system('start temp.txt')
    else: os.system('open temp.txt')

print('\nPress (right_ctrl) 4-5 times to Activate. ')
print('Press (left_ctrl) 4-5 times to Deactivate. \n')
while True:
    keystokes =[]

    klistener =keyboard.Listener(on_release=release_detection)
    klistener.start()
    klistener.join()

    if not keystokes[0]: sys.exit(0)

    cropping, cropped = False, False
    x_start, y_start, x_end, y_end = 0, 0, 0, 0

    image = pyscreenshot.grab()
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback("window", mouse_crop)
    
    while True:
        if cropped:
            cv2.destroyWindow('window')
            break
        i = image.copy()
        if not cropping:
            cv2.imshow("window", image)
        elif cropping:
            cv2.rectangle(i, (x_start, y_start), (x_end, y_end), (0, 255, 0), 1)
            cv2.imshow("window", i)
        cv2.waitKey(1)
