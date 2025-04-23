import RPi.GPIO as GPIO
import time
from python.HR8825 import HR8825
from guizero import App, Text, PushButton, Combo, info, Window, TextBox

# Initialize motors
Motor1 = HR8825(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
Motor1.SetMicroStep('hardward', 'fullstep')

# Default values
volume = 120  # Volume of puffs in mL
inhale_time = 3  # Time of inhale in seconds
exhale_time = 2  # Time of exhale in seconds
in_flowrate = volume / inhale_time
out_flowrate = volume / exhale_time
hold_time = 0.5  # Hold time between inhale/exhale in seconds
interpuff_time = 18  # Time between puffs in seconds
number_puffs = 80

# Constraints
max_volume = 450  # Max volume of syringe

# Motor control functions
def inhale(motor, steps, speed):
    """Forward motion = inhale"""
    motor.TurnStep(Dir='forward', steps=steps, stepdelay=speed)

def hold(duration):
    """Pause for the specified duration."""
    time.sleep(duration)

def exhale(motor, steps, speed):
    """Backward motion = exhale"""
    motor.TurnStep(Dir='backward', steps=steps, stepdelay=speed)

def puff_sequence(motor, num_puffs, steps_forward, steps_backward, inhale_delay, exhale_delay, hold_time, interpuff_time):
    """Performs puff sequence for specified number of puffs"""
    for i in range(num_puffs):
        print(f"Performing puff {i + 1} of {num_puffs}")
        inhale(motor, steps_forward, inhale_delay)
        hold(hold_time)
        exhale(motor, steps_backward, exhale_delay)
        hold(interpuff_time)
    motor.Stop()
    print(f"Puffs complete")

# GUI Functions
def calculate_parameters():
    global volume, inhale_time, exhale_time, in_flowrate, out_flowrate

    selected_option = param_combo.value

    if selected_option == "Volume and Flowrates":
        volume = float(volume_input.value)
        in_flowrate = float(in_flowrate_input.value)
        out_flowrate = float(out_flowrate_input.value)
        inhale_time = volume / in_flowrate
        exhale_time = volume / out_flowrate
        
        inhale_time_input.value = round(inhale_time, 2)
        exhale_time_input.value = round(exhale_time, 2)

    elif selected_option == "Volume and Times":
        volume = float(volume_input.value)
        inhale_time = float(inhale_time_input.value)
        exhale_time = float(exhale_time_input.value)
        in_flowrate = volume / inhale_time
        out_flowrate = volume / exhale_time
        
        in_flowrate_input.value = round(in_flowrate, 2)
        out_flowrate_input.value = round(out_flowrate, 2)

    elif selected_option == "Flowrates and Times":
        in_flowrate = float(in_flowrate_input.value)
        out_flowrate = float(out_flowrate_input.value)
        inhale_time = float(inhale_time_input.value)
        exhale_time = float(exhale_time_input.value)
        
        inhale_volume = in_flowrate * inhale_time
        exhale_volume = out_flowrate * exhale_time
        
        if round(inhale_volume,2) != round(exhale_volume,2):
            info("Error", "Inhale and exhale volumes must match. Adjust flow rates or times")
            return None
            
        volume = inhale_volume
        volume_input.value = round(volume, 2)

    # Recalculate motor steps and delays
    revolutions_forward = volume * (1 / 23.077)
    revolutions_backward = volume * (1 / 23.077)
    steps_forward = int(revolutions_forward * 200)
    steps_backward = int(revolutions_backward * 200)
    inhale_delay = (inhale_time/2) / steps_forward
    exhale_delay = (exhale_time/2) / steps_backward

    return steps_forward, steps_backward, inhale_delay, exhale_delay

def start_puffing():
    global interpuff_time, number_puffs

    # Read values from sliders
    interpuff_time = float(interpuff_input.value)
    number_puffs = int(number_puffs_input.value)

    # Calculate the parameters based on user inputs
    steps_forward, steps_backward, inhale_delay, exhale_delay = calculate_parameters()

    if volume > max_volume:
        info("Error", f"Volume cannot exceed {max_volume} mL. Please select a lower volume.")
        return

    try:
        # Perform puff sequence
        puff_sequence(Motor1, number_puffs, steps_forward, steps_backward, inhale_delay, exhale_delay, hold_time, interpuff_time)
        info("Success", "Puff sequence complete.")
    except Exception as e:
        info("Error", f"An error occurred: {e}")
        Motor1.Stop()

def update_input_fields():
    """Update the visible input fields based on the selected parameter combination."""
    selected_option = param_combo.value

    # Hide or show fields based on the selected option
    if selected_option == "Volume and Times":
        in_flowrate_input.disable()
        out_flowrate_input.disable()
        volume_input.enable()
        inhale_time_input.enable()
        exhale_time_input.enable()
    
    elif selected_option == "Volume and Flowrates":
        inhale_time_input.disable()
        exhale_time_input.disable()
        volume_input.enable()
        in_flowrate_input.enable()
        out_flowrate_input.enable()

    elif selected_option == "Flowrates and Times":
        volume_input.disable()
        in_flowrate_input.enable()
        out_flowrate_input.enable()
        inhale_time_input.enable()
        exhale_time_input.enable()
        
    calculate_parameters()
    
def real_time_update():
    #real time update
    calculate_parameters()
        

# GUI Setup
app = App(title="Puff Control GUI", width=400, height=450)

Text(app, "Select input parameters")
param_combo = Combo(app, options=["Volume and Times", "Volume and Flowrates", "Flowrates and Times"], command=update_input_fields)

Text(app, "Volume (mL)")
volume_input = TextBox(app, text=str(volume))

Text(app, "Inhale Flowrate (mL/sec)")
in_flowrate_input = TextBox(app, text=str(in_flowrate))

Text(app, "Exhale Flowrate (mL/sec)")
out_flowrate_input = TextBox(app, text=str(out_flowrate))

Text(app, "Inhale Time (sec)")
inhale_time_input = TextBox(app, text=str(inhale_time))

Text(app, "Exhale Time (sec)")
exhale_time_input = TextBox(app, text=str(exhale_time))

Text(app, "Interpuff Time (sec)")
interpuff_input = TextBox(app, text=str(interpuff_time))

Text(app, "Number of Puffs")
number_puffs_input = TextBox(app, text=str(number_puffs))

PushButton(app, text="Start Puffing", command=start_puffing)

# Initially disable irrelevant inputs
update_input_fields()

app.display()
