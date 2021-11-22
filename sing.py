#sing!!!!!!!!!!
import PySimpleGUI as sg
import pyaudio  #record /play stream
import numpy as np
import wave  # read far end wav file
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.io import wavfile
from scipy.signal import lfilter
# VARS CONSTS:
_VARS = {'window': False,
            'recordStream': False,        # near end recording
            'playStream': False,  # far end playing
            'errOutStream': False,  # err out playing at headset
            'MIC1Data': np.array([]), #near end (plot)  # from recording
            'MIC1Data_prev': np.array([]),
            'MIC1Data_acc': np.array([]), #near end (plot)   for subplot(211)
            'MIC2Data': np.array([]), #near end (plot)  # from recording
            'MIC2Data_acc': np.array([]), #near end (plot)   for subplot(212)
            
            'MIC1_DATA_all': np.array([]),  # for debug

            'pltCNT': False,  #count for subplot(212)
            'fig_agg': False,
            'pltFig': False,
            'ax': False,
            'ax2': False,
            'xData': False,
            'xData_acc': False,  
            'Line_h_lms': False,
            'h_lmsPLT': False,

            'pltRANGE': False,
            'h_LMS': False,   #np.zeros(160),
            'b_ECHO': False
            }

# pysimpleGUI INIT:
AppFont = 'Any 16'
sg.theme('LightBlue3') # LightBlue3 # DarkBlack  #DarkBlue3
# INIT vars:
CHUNK = 128  # Samples: 1024,  512, 256, 128
#RATE =16000# 44100  # according to the wav file
INTERVAL = 1  # Sampling Interval in Seconds ie Interval to listen
TIMEOUT = 10  # In ms for the event loop
SIZE_X= CHUNK
SIZE_Y=33500

layout = [  [sg.Canvas(key='figCanvas')],   # for matplotlib        
            #[sg.ProgressBar(4000, orientation='h', size=(20, 20), key='-PROG-')],
            [sg.Button('Start', font=AppFont),
            sg.Button('Stop', font=AppFont, disabled=True),
            sg.Button('Exit', font=AppFont),
            #sg.Text('Choose wav files',size=(15, 1), font=AppFont),
            #sg.Combo(['bumbleBEE_8k_short','SP03_8k','SP02_8k', 'SP01_8k',
            #          'bumbleBEE_8k','TakeOn_Me_8k'], default_value='SP01_8k',
            #size=(18, 1), font=AppFont, key='farendFile')
             ],
                        
            [sg.Text('echo level',size=(18, 1), font=AppFont),
            sg.Combo(['1','0.8','0.5','0.2','0'], default_value='1',size=(7, 1), font=AppFont, key='echo') ,

            [sg.Text('output Device',size=(15, 1), font=AppFont),
            sg.Combo(['2','3','4','5','6','7','8','9','10','11','12'], default_value='5',size=(4, 1), font=AppFont, key='outID') ,

            sg.Text('Mic.',size=(7, 1), font=AppFont),
            sg.Combo(['1','2','3','4','5','6','7'], default_value='1',size=(4, 1), font=AppFont, key='inID')]
            ]
            ]

_VARS['window'] = sg.Window('karaoke', layout, finalize=True,
            location=(400, 120), icon='SE.ico' )

# \\  -------- PYPLOT -------- //  # for matplotlib
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)  
    return figure_canvas_agg

def drawPlot():
    _VARS['pltFig'] = plt.figure( figsize=(10.3, 5.1))

    _VARS['ax'] = _VARS['pltFig'].add_subplot(211)
    _VARS['Line_MIC1'], = _VARS['ax'].plot(_VARS['xData_acc'], _VARS['MIC1Data_acc'], 'k', label = 'Mic 1')

    plt.xlim(-2,_VARS['pltRANGE']*SIZE_X+2)
    plt.ylim(-SIZE_Y, SIZE_Y)
    plt.yticks(np.arange(-32768, 32769, 16384))
    _VARS['ax'].legend(loc='upper left')
    
    _VARS['ax2'] = _VARS['pltFig'].add_subplot(212)
    _VARS['Line_MIC2'], = _VARS['ax2'].plot(_VARS['xData_acc'], _VARS['MIC1Data_acc'], 'k', label = 'Mic 2')
    plt.xlim(-2,_VARS['pltRANGE']*SIZE_X+2)
    plt.ylim(-SIZE_Y, SIZE_Y)
    plt.yticks(np.arange(-32768, 32769, 16384))

    _VARS['ax2'].legend(loc='upper left')

    plt.tight_layout()
    _VARS['fig_agg'] = draw_figure( _VARS['window']['figCanvas'].TKCanvas, _VARS['pltFig'])

def updatePlot():

    if(_VARS['pltCNT']>_VARS['pltRANGE']-1):
        _VARS['pltCNT']=0
        _VARS['MIC1Data_acc'] = np.zeros( _VARS['pltRANGE']*CHUNK).astype(np.int16)  # reset


    _VARS['MIC1Data_acc'][ _VARS['pltCNT']*CHUNK : (_VARS['pltCNT']+1)*CHUNK : ] = _VARS['MIC1Data']
    _VARS['Line_MIC1'].set_ydata(_VARS['MIC1Data_acc'])  # subplot(211)
    _VARS['Line_MIC2'].set_ydata(_VARS['MIC1Data_acc'])  # subplot(212)

    _VARS['pltCNT']=_VARS['pltCNT']+1
    
    _VARS['pltFig'].canvas.draw()
    _VARS['pltFig'].canvas.flush_events()
    
    
# \\  -------- PYPLOT -------- //

# INIT
rec_pAud = pyaudio.PyAudio()  #for near end playing
rec_pAud.get_default_output_device_info()
info = rec_pAud.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range (0,numdevices):
    if rec_pAud.get_device_info_by_host_api_device_index(0,i).get('maxInputChannels')>0:
        print("Input Device id ", i, " - ", rec_pAud.get_device_info_by_host_api_device_index(0,i).get('name'))

    if rec_pAud.get_device_info_by_host_api_device_index(0,i).get('maxOutputChannels')>0:
        print("Output Device id ", i, " - ", rec_pAud.get_device_info_by_host_api_device_index(0,i).get('name'))

errpAud = pyaudio.PyAudio()  #for err output playing

_VARS['b_ECHO'] = np.zeros(360)
_VARS['b_ECHO'][0]=1
_VARS['b_ECHO'][119]=0.8
_VARS['b_ECHO'][239]=0.4
_VARS['b_ECHO'][359]=0.2

# INIT Pyplot:
plot_flag = 1
_VARS['pltRANGE']=54
_VARS['pltCNT'] =0# _VARS['pltRANGE']-2   # range from 0~53
plt.style.use( 'seaborn-white')   #'dark_background' 'ggplot' , 'seaborn-darkgrid'
#https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html

_VARS['MIC1Data'] = np.zeros(CHUNK).astype(np.int16)  # INIT
_VARS['errOut'] = np.zeros(CHUNK).astype(np.int16)  # INIT
_VARS['DTD_data'] = np.zeros(CHUNK).astype(np.int16)  # INIT

_VARS['xData'] = np.linspace(0, CHUNK, num=CHUNK, dtype=int)
_VARS['xData_acc'] = np.linspace(0, _VARS['pltRANGE']*CHUNK, num=_VARS['pltRANGE']*CHUNK, dtype=int)
_VARS['MIC1Data_acc'] = np.zeros(_VARS['pltRANGE']*CHUNK).astype(np.int16)  # INIT
_VARS['MIC2Data_acc'] = np.zeros(_VARS['pltRANGE']*CHUNK).astype(np.int16)  # INIT
_VARS['DTD_acc'] = np.zeros(_VARS['pltRANGE']*CHUNK).astype(np.int16)  # INIT
_VARS['h_lmsPLT']=np.zeros(160)
near_buff_outside = np.zeros(2*CHUNK).astype(np.int16)  
drawPlot()   


def resetGlobalVar():
    # Reset global var
    _VARS['MIC1Data']= np.zeros(CHUNK).astype(np.int16)
    _VARS['MIC1Data_prev']= np.zeros(CHUNK).astype(np.int16)
    _VARS['MIC2Data']=np.zeros(CHUNK).astype(np.int16) 
    _VARS['MIC1_DATA_all'] = np.array([]).astype(np.int16)  # for debug

# GUI functions: 
def stop():
    if _VARS['recordStream']:
        _VARS['recordStream'].stop_stream()
        _VARS['recordStream'].close()

    if _VARS['errOutStream']:
        _VARS['errOutStream'].stop_stream()
        _VARS['errOutStream'].close()
    
    _VARS['window'].FindElement('Stop').Update(disabled=True)
    _VARS['window'].FindElement('Start').Update(disabled=False)


def recordCallback(in_data, frame_count, time_info, status):
    #mic1INPUT= np.frombuffer(in_data, dtype=np.int16)
#    _VARS['MIC1_DATA_all'] = np.concatenate((_VARS['MIC1_DATA_all'] , _VARS['MIC1Data'] ) )  # for debug
    #out1 = np.concatenate(( _VARS['MIC1Data_prev'][CHUNK-359:] , mic1INPUT ) )
    #_VARS['MIC1Data_prev'] = mic1INPUT
     
    #_VARS['MIC1Data'] = lfilter(_VARS['b_ECHO'] ,1,out1)
    #_VARS['MIC1Data'] = _VARS['MIC1Data'][359:]
    _VARS['MIC1Data']= np.frombuffer(in_data, dtype=np.int16)
    return (in_data, pyaudio.paContinue)


def play_Err_NearEnd_Callback(in_data, frame_count, time_info, status):
    
    try:
        # len according to far end wav file
        data = np.zeros(2*CHUNK).astype(np.int16)
        data[::2]=_VARS['MIC1Data'] 
        data[1::2]=_VARS['MIC1Data']   # or MIC 2 
        data = np.chararray.tobytes(data.astype(np.int16))

    except:
        data = np.zeros(len(data)).astype(np.int16)
        data[::2]=_VARS['MIC1Data'] 
        data[1::2]=_VARS['MIC1Data']   # or MIC 2 
        data = np.chararray.tobytes(data.astype(np.int16))

    return (data, pyaudio.paContinue)

def record_and_play():
    _VARS['window'].FindElement('Stop').Update(disabled=False)
    _VARS['window'].FindElement('Start').Update(disabled=True)

    # -----------INIT AEC-----------
    resetGlobalVar()
    fs=16000

    #-------------------------------------------
        
    _VARS['recordStream'] = rec_pAud.open(
                format=pyaudio.paInt16,  # prepare for record near end in real time
                channels=1,
                rate=fs,
                input=True,
                input_device_index =int(values['inID']),
                frames_per_buffer=CHUNK,
                stream_callback=recordCallback)
    
    
    _VARS['errOutStream'] = errpAud.open(
                format=pyaudio.paInt16,# prepare for err out playing
                channels=2,  # result output
                rate=fs,  
                output=True,
                output_device_index =int(values['outID']),
                stream_callback=play_Err_NearEnd_Callback)
    
    _VARS['recordStream'].start_stream()
    _VARS['errOutStream'].start_stream()


# MAIN LOOP
while True:
    event, values = _VARS['window'].read(timeout=TIMEOUT)
    if event == sg.WIN_CLOSED or event == 'Exit':
        stop()
        rec_pAud.terminate()
        errpAud.terminate()
        break
    if event == 'Start':
        record_and_play()
        plot_flag = 0
    if event == 'Stop':
        stop()
        plot_flag = 1

    #elif _VARS['MIC1Data'].size != 0:
        #updatePlot()     # for accumulation plot
        
    _VARS['b_ECHO'][119]=0.8*float(values['echo'])
    _VARS['b_ECHO'][239]=0.4*float(values['echo'])
    _VARS['b_ECHO'][359]=0.2*float(values['echo'])

_VARS['window'].close()

