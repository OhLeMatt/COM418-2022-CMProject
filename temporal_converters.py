import mido
import numpy as np

from utils import is_iterable
          
class TicksConverter:
    
    class Modes:
        OBJECT = 0
        OUTPUT = 1
        INPUT = 2
        TICKS = 2
    
    OBJECT_ID = 0
    OUTPUT_ID = 1
    INPUT_ID = 2
    NEXT_OUTPUT_ID = 3
    NEXT_INPUT_ID = 4
    
    # TARGET_INPUT_ID = 0
    # TARGET_NEXT_INPUT_ID = 1
    # TARGET_OUTPUT_ID = 2
    # Target mode to IDS
    TO_ID = [[2, 4, 1], # To Object
            [2, 4, 1], # To Output
            [1, 3, 2]] # To Input
    
    
    def __init__(self, 
                 messages_with_ticks, ticks_per_beat,
                 get_object_function, to_input_function, to_output_function, 
                 default_object, default_output=0, default_input=0):
        self.ticks_per_beat = ticks_per_beat
        # Based on modes
        self.functions = [lambda x, y, object: object, 
                          to_output_function,
                          to_input_function]
        
        self.events = [[get_object_function(message), 
                                None, 
                                message.time,
                                None, 
                                None]
                                for message in messages_with_ticks]
        
        current_object = default_object
        current_output = default_output
        current_input = default_input
        
        if len(self.events) == 0 or self.events[0][self.INPUT_ID] != default_input:
            self.events.insert(0, [current_object, 
                                    current_output, 
                                    current_input, 
                                    None, 
                                    None])
        else:
            current_object = self.events[0][self.OBJECT_ID]
        
        last_event = None
        for event in self.events:
            current_output += self.functions[self.Modes.OUTPUT](event[self.INPUT_ID], ticks_per_beat, current_object)
            current_input += event[self.INPUT_ID]
            current_object = event[self.OBJECT_ID]
            event[self.OUTPUT_ID] = current_output
            event[self.INPUT_ID] = current_input
            if last_event is not None:
                last_event[self.NEXT_INPUT_ID] = event[self.INPUT_ID]
                last_event[self.NEXT_OUTPUT_ID] = event[self.OUTPUT_ID]
            last_event = event
        if last_event is not None:
            last_event[self.NEXT_INPUT_ID] = np.inf
            last_event[self.NEXT_OUTPUT_ID] = np.inf
            
        self.event_count = len(self.events)
        self.prev_event = self.events[0]
        
    
    
    def convert(self, input, target_mode=Modes.OUTPUT):
        input_id, next_input_id, output_id = self.TO_ID[target_mode]
        if not is_iterable(input):
            if input < 0:
                return self.functions[target_mode](input, self.ticks_per_beat, self.events[0][self.OBJECT_ID])
            
            for event in [self.prev_event] + self.events:
                diff_input = input - event[input_id]
                base = event[output_id]
                if diff_input >= 0 and input < event[next_input_id]:
                    self.prev_event = event
                    if target_mode > 0:
                        return base + self.functions[target_mode](diff_input, self.ticks_per_beat, event[self.OBJECT_ID])
                    else:
                        return self.functions[target_mode](diff_input, self.ticks_per_beat, event[self.OBJECT_ID])
                            
        else: # Assumes a sorted list 
            result = []
            event = self.events[0]
            base = event[output_id] if target_mode > 0 else 0
            idx = 1
            for single_input in input:
                if single_input < 0:
                    result.append(self.functions[target_mode](single_input, self.ticks_per_beat, self.events[0][self.OBJECT_ID]))
                else:
                    diff_input = single_input - event[input_id]
                    
                    while idx < self.event_count and not (diff_input >= 0 and single_input < event[next_input_id]):
                        event = self.events[idx]
                        base = event[output_id]
                        diff_input = single_input - event[input_id]
                        idx += 1
                    
                    if target_mode > 0:
                        result.append(base + self.functions[target_mode](diff_input, self.ticks_per_beat, event[self.OBJECT_ID]))
                    else:
                        result.append(self.functions[target_mode](diff_input, self.ticks_per_beat, event[self.OBJECT_ID]))
                    
            return result
    
DEFAULT_TEMPO = 500000    

def tick2time(ticks, ticks_per_beat, tempo):
    return ticks / ticks_per_beat * tempo / 1e6

def time2tick(bartime, ticks_per_beat, tempo):
    return round(bartime * ticks_per_beat / tempo * 1e6)

class TicksTimeConverter(TicksConverter):
    
    def __init__(self, tempos_with_ticks, ticks_per_beat):
        super().__init__(messages_with_ticks=tempos_with_ticks, 
                         ticks_per_beat=ticks_per_beat,
                         get_object_function=lambda message: message.tempo,
                         to_input_function=time2tick,
                         to_output_function=tick2time,
                         default_object=DEFAULT_TEMPO,
                         default_output=0.0)
        
    def to_ticks(self, time):
        return self.convert(time, self.Modes.INPUT)
    
    def to_tempo(self, ticks):
        return self.convert(ticks, self.Modes.OBJECT)
    
    def to_time(self, ticks):
        return self.convert(ticks, self.Modes.OUTPUT)
        

def tick2bartime(ticks, ticks_per_beat, timesig):
    return ticks / ticks_per_beat / timesig[0] * timesig[1] / 4

def bartime2tick(bartime, ticks_per_beat, timesig):
    return round(bartime * ticks_per_beat * timesig[0] / timesig[1] * 4)

DEFAULT_TIMESIG = (4,4)

class TicksBartimeConverter(TicksConverter):
    def __init__(self, timesigs_with_ticks, ticks_per_beat):
        super().__init__(messages_with_ticks=timesigs_with_ticks, 
                         ticks_per_beat=ticks_per_beat,
                         get_object_function=lambda message: (message.numerator,message.denominator),
                         to_input_function=bartime2tick,
                         to_output_function=tick2bartime,
                         default_object=DEFAULT_TIMESIG,
                         default_output=0.0)
    
    def to_ticks(self, bartime):
        return self.convert(bartime, self.Modes.INPUT)
    
    def to_timesig(self, ticks):
        return self.convert(ticks, self.Modes.OBJECT)
    
    def to_bartime(self, ticks):
        return self.convert(ticks, self.Modes.OUTPUT)
          
if __name__ == "__main__":
    ticks_per_beat = 100
    
    tempos_with_ticks = [
        mido.MetaMessage("set_tempo", tempo=DEFAULT_TEMPO + ticks + 2000, time=ticks)
        for ticks in range(0, 1000, 100)
    ]
    # tempos_with_ticks = [mido.MetaMessage("set_tempo", tempo=850000, time=0)]
    
    time_conv = TicksTimeConverter(tempos_with_ticks=tempos_with_ticks,
                                   ticks_per_beat=ticks_per_beat)
    
    
    timesigs_with_ticks = [
        mido.MetaMessage("time_signature", numerator=4, denominator=2**((ticks + 200)//200), time=ticks)
        for ticks in range(0, 1000, 200)
    ]
    # timesigs_with_ticks = [mido.MetaMessage("time_signature", numerator=2, denominator=4, time=0)]
    
    bartime_conv = TicksBartimeConverter(timesigs_with_ticks=timesigs_with_ticks, 
                                        ticks_per_beat=ticks_per_beat)
    
    ticks_list = [ticks for ticks in range(0, 1000, 25)]
    
    for ticks in ticks_list:
        time = time_conv.to_time(ticks)
        original_value = time_conv.to_ticks(time)
        tempo = time_conv.to_tempo(ticks)
        print(ticks, time, original_value, tempo)
    
    time_list = time_conv.to_time(ticks_list)
    ticks_list_from_time = time_conv.to_ticks(time_list)
    print(time_list)
    print(ticks_list_from_time)
        
    for ticks in ticks_list:
        bartime = bartime_conv.to_bartime(ticks)
        original_value = bartime_conv.to_ticks(bartime)
        timesig = bartime_conv.to_timesig(ticks)
        print(ticks, bartime, original_value, timesig)
    
    bartime_list = bartime_conv.to_bartime(ticks_list)
    ticks_list_from_bartime = bartime_conv.to_ticks(bartime_list)
    print(bartime_list)
    print(ticks_list_from_bartime)
        

