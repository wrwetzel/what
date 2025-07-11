#!/usr/bin/env python
# -------------------------------------------------------------------------------------
#   Player.py WRW 12-June-2025 - Moved from Hearing-Test.py to separate module.

#   This was developed several years ago. Includes a lot of music-related code not
#   used for hearing test. Keep for possible future use.

# -------------------------------------------------------------------------------------

import numpy as np
import re
import copy
import math

# -------------------------------------------------------------------------------------

class Player():
    def __init__(self):
        self.concert_a4 = 440
        self.fs = 44100             # 44100 samples/second
        self.notes_in_octave = 12
        self.starting_pitch = self.concert_a4 / (2**4)        # Start four octaves below a4
        self.waveshape = 'sin'
        self.envelope = 'linear'
        self.scale = self.make_chromatic_88( self.starting_pitch, self.notes_in_octave )
        self.show_graph = False
        self.plot_exists = False
        self.tempo = 120

    def set_tempo( self, v ):     # beats per minute. 120 == .5 second notes, value of 1/4 note.
        self.tempo = v

    def set_scale( self, s ):
        self.scale = s

    def set_notes_in_octave( self, v ):
        self.notes_in_octave = v
        self.scale = self.make_chromatic_88( self.starting_pitch, self.notes_in_octave )

    def value2dur( self, value ):           # Convert note value, 1, 2, 4, 8, 16, ... to duration in seconds.
        dur = 60 / self.tempo / (value/4)   #   4 is 1/4 note, 1 beat at tempo.
        return dur

    def set_waveshape( self, v ):           # sin, saw, square
        self.waveshape = v

    def set_show_graph( self, v ):           # True to show graph
        self.show_graph = v

    def set_envelope( self, **kwargs ):             # 'triangle', 'linear', 'geometric', 'none', or array of [ start, end, dur ]
        if 'adsr' in kwargs:
            self.envelope = kwargs[ 'adsr' ]
            self.envelope_type = 'adsr'

        elif 'prop' in kwargs:
            self.envelope = kwargs[ 'prop' ]
            self.envelope_type = 'prop'

        elif 'shape' in kwargs:
            self.envelope = kwargs[ 'shape' ]
            self.envelope_type = 'shape'

    def make_chromatic_88( self, start, root ):     # Make an 88 note chromatic scale based on the root root of 2 starting at start
        results = []
        freq = start
        interval = 2**(1/root)
    
        for i in range( 0, 88 ):
            results.append(freq)
            freq *= interval
    
        return results

    # ------------------------------------------------
    #   Transformations on melody
    # ------------------------------------------------
    #   Reverse order of notes.

    def reverse( self, a ):
        a = re.sub( r"[\(\[].*?[\)\]]", "", a )       # Remove comments
        notes = a.split()      # Split on white space into individual notes
        return " ".join( notes[::-1] )

    # ------------------------------------------------
    #   Invert melody about a pivot note.

    def invert( self, a, pivot ):
        a = re.sub( r"[\(\[].*?[\)\]]", "", a )       # Remove comments
        notes = a.split()      # Split on white space into individual notes

        pivot_pitch, pivot_octave, _ = self.parse_note( pivot )

        pivot_note_num = self.get_note_num( pivot_pitch, pivot_octave )

        inv_notes = []
        for note in notes:
            pitch, octave, value = self.parse_note( note )

            if pitch == 'r':
                inv_notes.append( note )
            else:
                note_num = self.get_note_num( pitch, octave )
                inv_note_num = pivot_note_num - ( note_num - pivot_note_num )
                inv_note = self.make_note_from_index( inv_note_num, value )
                inv_notes.append( inv_note )

        return " ".join( inv_notes )

    # ------------------------------------------------
    #   Change note duration by integer factor

    def alter_value( self, a, factor ):
        a = re.sub( r"[\(\[].*?[\)\]]", "", a )       # Remove comments
        notes = a.split()      # Split on white space into individual notes

        alt_notes = []
        for note in notes:
            pitch, octave, value = self.parse_note( note )
            # value = int( value / factor )
            value = int( round( value / factor, 0 ))
            alt_note = pitch + str(octave) + "/" + str(value)
            alt_notes.append( alt_note )

        return " ".join( alt_notes )

    # ------------------------------------------------
    #   Shift pitch up or down by inter value shift

    def alter_pitch( self, a, shift ):
        a = re.sub( r"[\(\[].*?[\)\]]", "", a )       # Remove comments
        notes = a.split()      # Split on white space into individual notes

        alt_notes = []
        for note in notes:
            pitch, octave, value = self.parse_note( note )

            if pitch == 'r':
                inv_notes.append( note )
            else:
                note_num = self.get_note_num( pitch, octave )
                alt_note_num = note_num + shift

                if alt_note_num < 0:
                    alt_note_num = 0;
                if alt_note_num >= 88:
                    alt_note_num = 88;

                alt_note = self.make_note_from_index( alt_note_num, value )
                alt_notes.append( alt_note )

        return " ".join( alt_notes )

    # ------------------------------------------------

    def get_env_parameters( self, geometric_flag, amp_start, amp_end, segment_samples ):
        if geometric_flag:
            amp_start = max( amp_start, .01 )
            amp_end =   max( amp_end, .01 )
            delta_amp = (amp_end / amp_start) **(1/segment_samples)

        else:
            delta_amp = ( amp_end - amp_start ) / segment_samples

        return amp_start, delta_amp

    # ------------------------------------------------------------------------------
    #   Make a note from index and value, reverse of parse_note()

    def make_note_from_index( self, index, value ):
        note_offset = ( index + 9 ) % 12
        octave = ( index + 9 ) // 12

        return note_names[ note_offset ] + str(octave) + "/" + str(value)

    # ------------------------------------------------------------------------------
    #   Get the note number, i.e. index into scale, from pitch and octave.
    #   We can't go directly to note number in parse_note because of need to deal with rests.

    def get_note_num( self, pitch, octave ):
        return pitch_offset[ pitch ] - 9 + int( octave ) * 12

    # ------------------------------------------------
    #   Parse a note in text notation to pitch, octave, value
    #         1    2      4        5
    #       pitch octave [value 4] [dot none]

    def parse_note( self, note ):
        m = re.match( r'([cdefgabr][-+]?)([0-8])?(/([0-9]{1,2})(\.)?)?', note )
        if m:
            pitch = m.group(1)

            # ---------------------------------------
            if pitch == 'r':
                if m.group(4):
                    value = int( m.group(4) )
                else:
                    value = 4
                return pitch, None, value

            # ---------------------------------------
            octave = int( m.group(2) )

            # ---------------------------------------
            if m.group(4):
                value = int( m.group(4) )
            else:
                value = 4

            # ---------------------------------------
            #   dotted note is 1.5 note value

            if m.group(5) and m.group(5) == '.':
                value /= 1.5

            # ---------------------------------------

            return pitch, octave, value
        else:
            return None, None, None

    # ------------------------------------------------------------------------------

    def play_melody( self, melody, show ):
        waves_np = self.make_wave_from_notes( melody, show )
        self.play_wave( waves_np )

    # --------------------------------------------------------------
    #  note is one of: "c4/1 c+4/2 d4/4 d+4/8 e4/16 f4/32 f+4/3 g4 g+4 a4 a+4 b4 c5"

    def make_wave_from_notes( self, melody, show ):

        melody = re.sub( r"[\(\[].*?[\)\]]", "", melody )       # Remove comments

        notes = melody.split()      # Split on white space into individual notes

        if show:
            show_first = self.show_graph
        else:
            show_first = False

        waves_np = np.empty(0)

        for note in notes:
            if show:
                # print( note )
                pass

            pitch, octave, value = self.parse_note( note )
            if pitch == 'r':
                waves_np = np.append( waves_np, np.zeros( int(self.fs * self.value2dur( value ))))

            elif pitch:
                # print( "pitch: {n:s}, octave: {o:d}, dur: {v:d} dot: {dot:s}".format( n=pitch, o=octave, v=dur, dot=dot ) )

                note_num = self.get_note_num( pitch, octave )
                freq = self.scale[ note_num ]

                # print( "f: {p:4.2f} hz".format( p=freq ) )
                wave_np = self.make_wave_from_freq_dur( freq, self.value2dur( value ), show_first )     # *******************
                waves_np = np.append( waves_np, wave_np )
                show_first = False

            else:
                print( "ERROR: no match for '%s'" % note )

        return waves_np

    # --------------------------------------------------------------
    #   Play note of freq in hz for dur in seconds.
    #   show is typically True just for the first call from play_melody()

    def make_wave_from_freq_dur( self, freq, dur, show ):  # freq in hz, dur in seconds.

        time = np.linspace(0, dur, int(dur * self.fs), False)   # Generate array with dur*sample_rate elements, ranging between 0 and dur (in seconds)

        # ------------------------------------------------
        #   Select waveshape

        if self.waveshape == 'sin':
            wave_np = np.sin( time * freq * 2 * np.pi)    # Generate a sin wave of freq frequency in hz

        # elif self.waveshape == 'sawtooth':
        #     wave_np = signal.sawtooth( time * freq * 2 * np.pi )

        # elif self.waveshape == 'triangle':
        #     wave_np = signal.sawtooth( time * freq * 2 * np.pi, .5 )

        # elif self.waveshape == 'square':
        #     wave_np = signal.square( time * freq * 2 * np.pi )

        # ---------------------------------------------------------------------
        #   Get and apply envelope

        envelope_np = self.get_envelope( dur )
        wave_np *= envelope_np

        # ---------------------------------------------------------------------
        #   Apply Envelope
        # ---------------------------------------------------------------------
        #   Apply envelope specified by array of [ amp_start, amp_end, duration ]
        #   Example: p.set_envelope( [[0, 1, .2], [1, .5, .2], [.5, 0, .6]] )
        #   With 4 values: attack, decay, sustain, release
        #   RESUME - Option to give time values for above, not duration relative to entire note.

        # ------------------------------------------------
        if show:
            self.do_matplotlib_plot( time, wave_np )
            # self.do_pyqtgraph_plot( time, wave_np )

        # print( len(wave_np))
        return wave_np

    # --------------------------------------------------------------
    #   Make an envelope in a numpy array with values ranging from 0 to 1.
    #   Envelope duration of dur seconds. Attack, decay, and release specified in seconds. Sustain computed.
    #   attack              decay                sustain              release
    #   [[0, 1, .05, True], [1, .3, .05, True ], [.3, .2, .2, False], [.2, 0, .05, True]]

    #   initial amp, final amp, segment_duration, geometric_flag
    #   [0,          1,         .05,              True ]

    def get_envelope( self, dur ):

        env_np = np.empty( int(dur * self.fs) )     # Make array to hold envelope
        sample_count = len( env_np )

        if self.envelope_type == 'adsr':        # Absolute duration for all but sustain

            if len( self.envelope ) != 4:
                print( "ERROR: adsl envelope must have 4 parts: attack, decay, sustain, release" )
                sys.exit(0)

            #   Note duration may be less that specified attack, decay and release, shorten env in reverse order.

            adj_envelope = copy.deepcopy( self.envelope )
            e = adj_envelope

            attack_dur = e[0][2] 
            decay_dur  = e[1][2] 
            release_dur = e[3][2]
            sustain_dur = dur - ( attack_dur + decay_dur + release_dur )

            if sustain_dur < 0:
                sustain_dur = 0.0
                release_dur = dur - ( attack_dur + decay_dur )
                if release_dur < 0:
                    release_dur = 0
                    decay_dur = dur - attack_dur
                    if decay_dur < 0:
                        decay_dur = 0
                        attack_dur = dur

            adj_envelope[0][2] = attack_dur
            adj_envelope[1][2] = decay_dur
            adj_envelope[2][2] = sustain_dur
            adj_envelope[3][2] = release_dur

            start_sample = 0
            for amp_start, amp_end, segment_dur, geometric_flag in adj_envelope:

                segment_samples = int( self.fs * segment_dur )

                if segment_samples > 0:
                    amp_start, delta_amp = self.get_env_parameters( geometric_flag, amp_start, amp_end, segment_samples )

                    for i in range( start_sample , start_sample + segment_samples ):
                        if geometric_flag:
                            env_np[i]  = amp_start
                            amp_start *= delta_amp

                        else:
                            env_np[i] = amp_start
                            amp_start += delta_amp

                    start_sample += segment_samples

            # Can have round-off errors in the conversion of time to samples resulting in generating one less sample.

            if sample_count > start_sample:        # Check if we made the exact number of samples expected
                for i in range( start_sample, sample_count ):
                    env_np[i] = 0.0
                    start_sample += 1

            elif sample_count < start_sample:        # Check if we made the exact number of samples expected
                print( "NOTE: envelope too big, expected:", sample_count, "actual:", start_sample )

        # ---------------------------------------------------------------------

        elif self.envelope_type == 'prop':        # proportional to note length
            start_sample = 0
            i = 0

            for amp_start, amp_end, segment_dur, geometric_flag in self.envelope:
                segment_samples = sample_count * segment_dur
                amp_start, delta_amp = self.get_env_parameters( geometric_flag, amp_start, amp_end, segment_samples )

                for i in range( int( start_sample) , int( start_sample + segment_samples )):
                    if geometric_flag:
                        env_np[i]  = amp_start
                        amp_start *= delta_amp

                    else:
                        env_np[i] = amp_start
                        amp_start += delta_amp

                start_sample += segment_samples

            if sample_count - start_sample > 0:        #   If any remaining samples reduce to 0 according to last geometric_flag
                amp_start, delta_amp = self.get_env_parameters( geometric_flag, amp_start, 0, sample_count - start_sample )

                for i in range( int( start_sample) , sample_count ):
                    if geometric_flag:
                        env_np[i]  = amp_start
                        amp_start *= delta_amp
                    else:
                        env_np[i]  = amp_start
                        amp_start += delta_amp

        # ---------------------------------------------------------------------
        #   Apply one of few pre-defined envelopes

        elif self.envelope_type == 'shape':
            amp = 1.0

            if self.envelope == 'linear':            #   Linear envelope from 1 to 0
                delta_amp = 1/sample_count 
                for i in range( sample_count ):
                    env_np[i] = amp
                    amp -= delta_amp

            elif self.envelope == 'geometric':            #   geometric envelope from 1 to small value
                delta_amp = .1**(1/sample_count )
                for i in range( sample_count ):
                    env_np[i] = amp
                    amp *= delta_amp

            elif self.envelope == 'triangle':            #   symmetric triangle envelope
                amp = 0
                delta_amp = 1/(sample_count/2)
                half_len = int( sample_count/2 )
                for i in range( half_len ):
                    env_np[i] = amp
                    amp += delta_amp

                for i in range( half_len, sample_count  ):
                    env_np[i] = amp
                    amp -= delta_amp

        elif self.envelope_type == 'none':           #   no envelope
            pass

        else:
            print( "ERROR: Envelope shape type '%s' not recognized" % self.envelope )

        return env_np

    # --------------------------------------------------------------
    #   Play tone and wait for playback to finish
    #   Reduce signal to max integer range and convert to integers.

    def play_wave( self, wave_np ):

        #   Limit values and convert to 16-bits

        audio = wave_np * (2**15 - 1) / np.max( np.abs( wave_np ))   # Ensure that highest value is in 16-bit range
        audio = audio.astype( np.int16 ) # Convert to 16-bit data

        play_obj = sa.play_buffer(audio, 1, 2, self.fs)      # Start playback
        play_obj.wait_done()    # Wait for playback to finish before exiting

    # --------------------------------------------------------------

    def do_pyqtgraph_plot( self, time, note ):
        ## Always start by initializing Qt (only once per application)
        app = QtGui.QApplication([])
        
        ## Define a top-level widget to hold everything
        w = QtGui.QWidget()
        
        ## Create some widgets to be placed inside
        btn = QtGui.QPushButton('press me')
        text = QtGui.QLineEdit('enter text')
        listw = QtGui.QListWidget()
        plot = pg.PlotWidget()
        
        ## Create a grid layout to manage the widgets size and position
        layout = QtGui.QGridLayout()
        w.setLayout(layout)
        
        ## Add widgets to the layout in their proper positions
        layout.addWidget(btn, 0, 0)   # button goes in upper-left
        layout.addWidget(text, 1, 0)   # text edit goes in middle-left
        layout.addWidget(listw, 2, 0)  # list widget goes in bottom-left
        layout.addWidget(plot, 0, 1, 3, 1)  # plot goes on right side, spanning 3 rows
        
        ## Display the widget as a new window
        w.show()
        
        ## Start the Qt event loop
        app.exec_()

    # --------------------------------------------------------------
    #   Show plot of entire note and short sample from beginning
    #   Explored real-time updates but too slow when clearning plot.
    #   Alternative requires constant length x-axes.
    #   Look at pyQtGraph(), claims to be much faster.

    def do_matplotlib_plot( self, time, note ):
        if self.plot_exists:
            self.ax[0].clear()
            self.ax[1].clear()

        else:
            self.plot_exists = True
            self.fig, self.ax = plt.subplots( nrows=2, ncols=1, figsize=(10, 5))

        self.plt0, = self.ax[0].plot( time, note )
        self.ax[0].set_title( 'Entire note' )
        self.ax[0].set_ylim( [-1.1, 1.1] )

        self.plt1, = self.ax[1].plot( time[0:2000], note[0:2000] )
        self.ax[1].set_title( 'Initial part of note' )
        self.ax[1].set_ylim( [-1.1, 1.1] )

        self.fig.tight_layout()

        plt.draw()
        plt.pause( .01 )
        plt.ion()
        plt.show()

        # else:     # Much faster but all notes must be the same length
        #     self.plt0.set_ydata( note )
        #     self.plt1.set_ydata( note[0:2000] )
        #     self.fig.canvas.draw()
        #     self.fig.canvas.flush_events()

# -------------------------------------------------------------------------------------
