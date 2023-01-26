import mido
from sys import argv


def fold_left(list_of_a, zero_b, ba2b):
    if list_of_a:
        return fold_left(list_of_a[1:], ba2b(zero_b, list_of_a[0]), ba2b)
    else:
        return zero_b


class MidiEvnt:
    def __init__(self, note, time):
        self.note = note
        self.time = time

    def __str__(self):
        return f"MidiEvnt({self.time},{self.note})"


def to_events(filename):
    def get_velocity(m: mido.Message, default_value: int=0):
        try:
            return m.velocity
        except:
            return default_value

    return [[x.note, get_velocity(x), x.time] for x in filename.tracks[1] if
            isinstance(x, mido.Message)]


def to_timed_pitches(events):
    def f(b, original_event):
        actual_time = b[0]
        midi_events = b[1]

        event_note = original_event[0]
        event_velocity = original_event[1]
        event_time = original_event[2]

        next_time = actual_time + event_time
        next_midi_events = midi_events if event_velocity == 0 else midi_events + [MidiEvnt(event_note, next_time)]

        return [next_time, next_midi_events]

    init_midi_events: [MidiEvnt] = []
    init_time: int = 0
    return fold_left(events, [init_time, init_midi_events], f)[1]


def diff_of_same_note(event: MidiEvnt, events: [MidiEvnt], threshold_ms: int):
    def f(last_diff: int, evt: MidiEvnt):
        actual_diff = abs(evt.time - event.time)
        return actual_diff if actual_diff < threshold_ms and actual_diff < last_diff and evt.note == event.note else last_diff

    return fold_left(events, threshold_ms, f)


def calculate_avg_diff(control: [MidiEvnt], performance: [MidiEvnt], threshold_ms: int = 200):
    sum_of_diffs = sum([diff_of_same_note(md, performance, threshold_ms) for md in control])
    return float(sum_of_diffs) / len(control)


if __name__ == '__main__':
    path_perfect = argv[1]
    path_performance = argv[2]
    threshold = 100 if len(argv) < 4 else int(argv[3])

    mid_good = mido.MidiFile(path_perfect)
    mid_bad = mido.MidiFile(path_performance)

    timed_pitches_good = to_timed_pitches(to_events(mid_good))
    timed_pitches_bad = to_timed_pitches(to_events(mid_bad))

    diff = calculate_avg_diff(timed_pitches_good, timed_pitches_bad, threshold)
    percentage = 100 - (diff * 100.0 / threshold)
    print("control:", path_perfect)
    print("performance:", path_performance)
    print("threshold:", threshold)
    print("average difference in ms: ", diff)
    print("percentage: ", percentage)
