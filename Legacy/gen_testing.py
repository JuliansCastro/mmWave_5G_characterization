import asyncio
from pynput import keyboard
import time
from threading import Event
from pytictoc import TicToc

# async def main():
#     loop = asyncio.get_event_loop()
#     stop_event = asyncio.Event()
#     kill_event = asyncio.Event()

#     def on_key_press(key):
#         if key == keyboard.Key.esc:
#             stop_event.set()
#             print('Stopped...')
#         elif key == keyboard.Key.enter:
#             stop_event.clear()
#             print('Continuing...')
#         elif key == keyboard.KeyCode.from_char('k'):
#             print('Ending running')
#             kill_event.set()
#             print('Set? ', kill_event.is_set())
#         else:
#             print('No se reconoce como comando')

#     listener = keyboard.Listener(on_press=on_key_press)
#     listener.start()

#     print("Presiona 'esc' para detener el bucle...")

#     try:

#         while not kill_event.is_set():

#             while not (stop_event.is_set() or kill_event.is_set()):
#                 print('.')
#                 await asyncio.sleep(1)

#         listener.stop()
#         print('The end?')

#     except KeyboardInterrupt:

#         listener.stop()
#         print("Bucle detenido.")

# if __name__ == "__main__":
#     asyncio.run(main())


#     def on_key_press(key):
#         if key == keyboard.Key.esc:
#             stop_event.set()
#             print('Stopped...')
#         elif key == keyboard.Key.enter:
#             stop_event.clear()
#             print('Continuing...')
#         elif key == keyboard.KeyCode.from_char('k'):
#             print('Ending running')
#             kill_event.set()
#             print('Set? ', kill_event.is_set())
#         else:
#             print('No se reconoce como comando')



# measuring_flag = Event()
# timer = TicToc

def on_key_press(key):
    if key == keyboard.Key.esc:
        print('Stopped...')
        measuring_flag.set()
    elif key == keyboard.Key.enter:
        print('Continuing...')
        measuring_flag.clear()
    # else:
    #     print('No se reconoce como comando')

try:

    measuring_flag = Event()
    timer = TicToc()
    elapsed_time = 0

    key_listener = keyboard.Listener(on_press=on_key_press)
    key_listener.start()
    timer.tic()

    while True:
        
        timer.tocvalue(restart=True)
        # elapsed_time += timer.tocvalue(restart=True)
        while not measuring_flag.is_set():
            print('.')
            time.sleep(1)
            pending_time_sum = True
            # print(elapsed_time)
        
        if pending_time_sum:
            elapsed_time += timer.tocvalue()
            print(elapsed_time)
            pending_time_sum = False

except KeyboardInterrupt:
    print('Oh no')
finally:
    print('Closing system...')
    key_listener.stop()


