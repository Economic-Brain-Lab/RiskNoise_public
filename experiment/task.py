import argparse
import os.path as op
from psychopy.visual import Slider
from psychopy import event
from exptools2.core import PylinkEyetrackerSession, Trial
from utils import _create_stimulus_array, get_output_dir_str, DummyWaiterTrial, OutroTrial, get_settings
from instruction import InstructionTrial
from stimuli import FixationLines, ResponseSlider, ProbabilityPieChart
import numpy as np
import logging
from psychopy.visual import Line, Rect, TextStim

class ProbCueTrial(InstructionTrial):

    def __init__(self, session, trial_nr, prob, **kwargs):

        txt = session.instructions['prob_cue'].format(prob=int(prob*100))
        bottom_txt = ""

        self.prob_cue = ProbabilityPieChart(session.win,
                                            prob,
                                            session.settings['prob_cue'].get('cue_size'),
                                            pos=(0, -1.))

        super().__init__(session, trial_nr, txt, bottom_txt=bottom_txt,
                        phase_durations=[session.settings['durations']['cue_trials']],
                         **kwargs)

        self.text.pos = (0, 1.)
        self.text.alignText = 'center'

    def draw(self):
        super().draw()
        self.prob_cue.draw()

    def get_events(self):
        Trial.get_events(self)


class TaskTrial(Trial):
    def __init__(self, session, trial_nr, phase_durations=None,
                jitter=1,
                payoff=15, prob=0.55, **kwargs):

        if phase_durations is None:
            phase_durations = [session.settings['durations']['first_fixation'], # Red fixation
                               session.settings['durations']['second_fixation'],# Pie chart
                            session.settings['durations']['array_duration'],    # Doy display
                            jitter,                                 # ISI            
                            session.settings['durations']['response_screen'], # Response
                            session.settings['durations']['feedback'], # Feedback
                            0.0] #Spillover

        self.total_duration = np.sum(phase_durations)

        self.stimulus_phase = [2]
        self.response_phase = 4
        self.feedback_phase = 5

        phase_names = ['fixation1', 'prob_cue', 'stimulus', 'jitter', 'response', 'feedback', 'iti']

        super().__init__(session, trial_nr, phase_durations, phase_names=phase_names, **kwargs)

        self.parameters['prob'] = prob
        self.parameters['payoff'] = payoff
        self.parameters['jitter'] = jitter
        self.stimulus_array = _create_stimulus_array(self.session.win, self.parameters['payoff'],
                                                     self.session.settings['cloud'].get('aperture_radius'),
                                                     self.session.settings['cloud'].get('dot_radius'),)

        self.prob_cue = ProbabilityPieChart(self.session.win, self.parameters['prob'],
                                            self.session.settings['prob_cue'].get('cue_size'),
                                            include_text=False)

        if self.session.settings['task'].get('show_prob_during_payoff'):
            self.prob_fixation = ProbabilityPieChart(self.session.win, self.parameters['prob'],
                                                self.session.settings['prob_cue'].get('fixation_size'),
                                                include_text=False)


        self.parameters['start_marker_position'] = np.random.randint(self.session.settings['slider']['range'][0],
                                                                     self.session.settings['slider']['range'][1] + 1)

    def get_events(self):

        events = super().get_events()

    def draw(self):

        if self.session.win.mouseVisible:
            self.session.win.mouseVisible = False

        if (self.phase == self.feedback_phase) & (not hasattr(self, 'response_onset')):
            self.session.fixation_lines.draw(draw_fixation_cross=False)
        elif self.phase in self.stimulus_phase:
            self.session.fixation_lines.draw(draw_fixation_cross=False)
        else:
            self.session.fixation_lines.draw()

        response_slider = self.session.response_slider

        # Hide marker during all phases except response and feedback
        if self.phase < self.response_phase:
            response_slider.show_marker = False

        if self.phase == 0: # Fixation
            self.session.fixation_lines.setColor((-1, .5, -1), fixation_cross_only=True)
        elif self.phase == 1: # Prob cue
            self.session.fixation_lines.setColor((1, -1, -1), fixation_cross_only=True)
            self.prob_cue.draw()
        elif self.phase in self.stimulus_phase:

            if self.session.settings['task'].get('show_prob_during_payoff'):
                self.prob_fixation.draw()

            self.stimulus_array.draw()

        elif self.phase == (self.response_phase - 1):
            response_slider.setMarkerPosition(self.parameters['start_marker_position'])
            response_slider.show_marker = False
            # Reset marker color to normal (not feedback color from previous trial)
            response_slider.marker.inner_color = self.session.settings['slider'].get('color')

        elif self.phase == self.response_phase:
            response_slider.marker.inner_color = self.session.settings['slider'].get('color')
            response_slider.draw()

        elif self.phase == self.feedback_phase:
            if hasattr(self, 'response_onset'):
                response_slider.marker.inner_color = self.session.settings['slider'].get('feedbackColor')
                response_slider.draw()
            else:
                self.session.too_late_stimulus.draw()
                    
        self.previous_phase = self.phase


class TwoStageTasktrial(TaskTrial):

    def __init__(self, session, trial_nr, phase_durations=None,
                jitter=1,
                payoff=15, prob=0.55, **kwargs):

        if phase_durations is None:
            phase_durations = [session.settings['durations']['first_fixation'], # Red fixation
                               session.settings['durations']['second_fixation'],# Pie chart
                            session.settings['durations']['array_duration'],    # Doy display
                            jitter,                                 # ISI
                            session.settings['durations']['response_screen'], # Response 1
                            session.settings['durations']['feedback'], # Feedback 1
                            0.0, # Response 2
                            session.settings['durations']['feedback'], # Feedback 2
                            0.0] # Spillover


        super().__init__(session, trial_nr, phase_durations, jitter, payoff, prob, **kwargs)

        self.stimulus_phase = [2]
        self.response_phase1 = 4
        self.feedback_phase1 = 5
        self.response_phase2 = 6
        self.feedback_phase2 = 7

        self.parameters['start_marker_position'] = np.random.uniform(self.session.settings['slider']['range'][0],
                                                                self.session.settings['slider']['range'][1])

        self.phase_names = ['fixation1', 'prob_cue', 'stimulus', 'jitter', 'response1', 'feedback1',
                            'response2', 'feedback2', 'iti']


    def get_events(self):


        response_slider1 = self.session.response_slider1
        response_slider2 = self.session.response_slider2

        if self.phase == (self.response_phase1 - 1):

            if (not self.session.mouse.getPressed()[0]) and (self.session.mouse.getPos()[0] != response_slider1.marker.pos[0]):
                try:
                    self.session.mouse.setPos((response_slider1.marker.pos[0],0))
                    self.last_mouse_pos = response_slider1.marker.pos[0]
                except Exception as e:
                    print(e)

            self.last_mouse_pos = self.session.mouse.getPos()[0]/self.session.settings['interface']['mouse_multiplier']

        elif self.phase == self.response_phase1:

            if not hasattr(self, 'response_onset1'):
                current_mouse_pos = self.session.mouse.getPos()[0]/self.session.settings['interface']['mouse_multiplier']
                marker_position = response_slider1.mouseToMarkerPosition(current_mouse_pos)
                response_slider1.setMarkerPosition(marker_position)
                self.last_mouse_pos  = current_mouse_pos
                response_slider1.show_marker = True
                
                if self.session.mouse.getPressed()[0]:
                    self.response_onset1 = self.session.clock.getTime()
                    self.parameters['response_time1'] = self.response_onset1 - self.session.global_log.iloc[-1]['onset']
                    self.parameters['response1'] = response_slider1.marker_position

                    time_so_far = self.session.clock.getTime() - self.start_trial
                    self.phase_durations[self.feedback_phase1] = np.min((self.total_duration - time_so_far, self.phase_durations[self.feedback_phase1]))
                    self.phase_durations[self.response_phase2] = np.min((self.total_duration - time_so_far - self.phase_durations[self.feedback_phase1]))

                    range_length = response_slider1.range_[1] - response_slider1.range_[0]

                    response_slider2.range = (response_slider1.marker_position - response_slider1.width_proportion*range_length/2,
                                              response_slider1.marker_position + response_slider1.width_proportion*range_length/2)

                    response_slider2.setMarkerPosition(np.random.uniform(response_slider2.range[0], response_slider2.range[1]))


                    self.stop_phase()

        elif self.phase == self.response_phase2:

            if not hasattr(self, 'response_onset2'):
                current_mouse_pos = self.session.mouse.getPos()[0]/self.session.settings['interface']['mouse_multiplier']
                marker_position = response_slider2.mouseToMarkerPosition(current_mouse_pos)
                response_slider2.setMarkerPosition(marker_position)
                self.last_mouse_pos  = current_mouse_pos
                response_slider2.show_marker = True
                
                if self.session.mouse.getPressed()[0]:
                    self.response_onset2 = self.session.clock.getTime()
                    self.parameters['response_time2'] = self.response_onset2 - self.session.global_log.iloc[-1]['onset']
                    self.parameters['response'] = response_slider2.marker_position

                    time_so_far = self.session.clock.getTime() - self.start_trial
                    self.phase_durations[self.feedback_phase2] = np.min((self.total_duration - time_so_far, self.phase_durations[self.feedback_phase2]))
                    self.stop_phase()

        Trial.get_events(self)


    def draw(self):

        if self.session.win.mouseVisible:
            self.session.win.mouseVisible = False

        if (self.phase == self.feedback_phase) & (not hasattr(self, 'response_onset')):
            self.session.fixation_lines.draw(draw_fixation_cross=False)
        elif self.phase in self.stimulus_phase:
            self.session.fixation_lines.draw(draw_fixation_cross=False)
        else:
            self.session.fixation_lines.draw()

        response_slider1 = self.session.response_slider1
        response_slider2 = self.session.response_slider2

        # Hide markers during all phases except response and feedback
        if self.phase < self.response_phase1:
            response_slider1.show_marker = False
            response_slider2.show_marker = False

        if self.phase == 0: # Fixation
            self.session.fixation_lines.setColor((-1, .5, -1), fixation_cross_only=True)
        elif self.phase == 1: # Prob cue
            self.session.fixation_lines.setColor((1, -1, -1), fixation_cross_only=True)
            self.prob_cue.draw()
        elif self.phase in self.stimulus_phase:

            if self.session.settings['task'].get('show_prob_during_payoff'):
                self.prob_fixation.draw()

            self.stimulus_array.draw()

        elif self.phase == (self.response_phase1 - 1):
            response_slider1.setMarkerPosition(self.parameters['start_marker_position'])
            response_slider1.show_marker = False

        elif self.phase == self.response_phase1:
            response_slider1.marker.inner_color = self.session.settings['slider'].get('color')
            response_slider1.draw()

        elif self.phase == self.feedback_phase1:
            if hasattr(self, 'response_onset1'):
                response_slider1.marker.inner_color = self.session.settings['slider'].get('feedbackColor')
                response_slider1.draw()
                response_slider2.show_marker = False
            else:
                self.session.too_late_stimulus.draw()
        elif self.phase == self.response_phase2:
            response_slider2.marker.inner_color = self.session.settings['slider'].get('color')
            response_slider2.draw()
        elif self.phase == self.feedback_phase2:
            if hasattr(self, 'response_onset2'):
                response_slider2.marker.inner_color = self.session.settings['slider'].get('feedbackColor')
                response_slider2.draw()
            else:
                self.session.too_late_stimulus.draw()
                    
        self.previous_phase = self.phase

class TwoSliderTasktrial(TaskTrial):

    def __init__(self, session, trial_nr, phase_durations=None,
            jitter=1,
            payoff=15, prob=0.55, **kwargs):

        if phase_durations is None:
            phase_durations = [
                session.settings['durations']['first_fixation'],    # Red fixation
                session.settings['durations']['second_fixation'],   # Probability cue
                session.settings['durations']['array_duration'],    # Dot display
                jitter,                                             # ISI
                session.settings['durations']['response_screen'],   # Response 1
                0.0,                                                # Response 2
                session.settings['durations']['feedback'],          # Feedback 2
                0.0                                                 # Spillover
            ] 


        super().__init__(session, trial_nr, phase_durations, jitter, payoff, prob, **kwargs)

        self.stimulus_phase = [2]
        self.response_phase1 = 4
        self.response_phase2 = 5
        self.feedback_phase = 6

        self.parameters['start_marker_position'] = np.random.uniform(self.session.settings['slider']['range'][0],
                                                                self.session.settings['slider']['range'][1])

        self.phase_names = ['fixation1', 'prob_cue', 'stimulus', 'jitter', 'response1', 
                            'response2', 'feedback', 'iti'] 
        
    def get_events(self):

        events = super().get_events()

        response_slider1 = self.session.response_slider1
        response_slider2 = self.session.response_slider2

        if self.phase == (self.response_phase1 - 1):

            if (not self.session.mouse.getPressed()[0]) and (self.session.mouse.getPos()[0] != response_slider1.marker.pos[0]):
                try:
                    self.session.mouse.setPos((response_slider1.marker.pos[0],0))
                    self.last_mouse_pos = response_slider1.marker.pos[0]
                except Exception as e:
                    print(e)

            
        elif self.phase == self.response_phase1:

            response_slider2.show_marker = False
            response_slider2.marker.inner_color = self.session.settings['slider'].get('color')

            if not hasattr(self, 'response_onset1'):
                current_mouse_pos = self.session.mouse.getPos()[0]/self.session.settings['interface']['mouse_multiplier']
                marker_position = response_slider1.mouseToMarkerPosition(current_mouse_pos)
                response_slider1.setMarkerPosition(marker_position)
                self.last_mouse_pos  = current_mouse_pos
                response_slider1.show_marker = True
                
                if self.session.mouse.getPressed()[0]:
                    self.response_onset1 = self.session.clock.getTime()
                    self.parameters['response_time1'] = self.response_onset1 - self.session.global_log.iloc[-1]['onset']
                    self.parameters['response1'] = response_slider1.marker_position

                    left_edge = list(response_slider1.bins).index(response_slider1.marker_position)
                    right_edge = left_edge + 1
                    response_slider2.range = (response_slider1.bins[left_edge], 
                                              response_slider1.bins[right_edge])

                    self.phase_durations[self.response_phase2] = -self.session.timer.getTime()
                    self.stop_phase()

        elif self.phase == self.response_phase2:

            response_slider2.show_marker = True

            time_in_phase = self.session.timer.getTime() + self.phase_durations[self.response_phase2]

            if not hasattr(self, 'response_onset2'):
                current_mouse_pos = self.session.mouse.getPos()[0]/self.session.settings['interface']['mouse_multiplier']
                marker_position = response_slider2.mouseToMarkerPosition(current_mouse_pos)
                response_slider2.setMarkerPosition(marker_position)
                self.last_mouse_pos  = current_mouse_pos
                response_slider2.show_marker = True

                
                if (time_in_phase > .5) & self.session.mouse.getPressed()[0]:
                    self.response_onset2 = self.session.clock.getTime()
                    self.parameters['response_time2'] = self.response_onset2 - self.session.global_log.iloc[-1]['onset']
                    self.parameters['response'] = response_slider2.marker_position
                    self.session.response_slider2.marker.inner_color = self.session.settings['slider'].get('feedbackColor')

                    time_so_far = self.session.clock.getTime() - self.start_trial
                    self.phase_durations[self.feedback_phase] = np.min((self.total_duration - time_so_far, self.phase_durations[self.feedback_phase]))

                    self.stop_phase()


    def draw(self):

        if self.session.win.mouseVisible:
            self.session.win.mouseVisible = False

        if self.phase in self.stimulus_phase and self.session.settings['task'].get(
            'show_prob_during_payoff'
        ):
            self.session.fixation_lines.draw(draw_fixation_cross=False)
        elif self.phase != self.feedback_phase:
            self.session.fixation_lines.draw()

        # Hide markers during all phases except response and feedback
        if self.phase < 4:  # Before first response phase
            self.session.response_slider1.show_marker = False
            self.session.response_slider2.show_marker = False
        
        if self.phase == 0: # Fixation
            self.session.fixation_lines.setColor((-1, .5, -1), fixation_cross_only=True)
        elif self.phase == 1: # Prob cue
            self.session.fixation_lines.setColor((1, -1, -1), fixation_cross_only=True)
            self.prob_cue.draw()
        elif self.phase in self.stimulus_phase:
            if self.session.settings['task'].get('show_prob_during_payoff'):
                self.prob_fixation.draw()
            self.stimulus_array.draw()

        if self.phase in [4, 5]:  # Response phases only
            self.session.response_slider1.draw()
            self.session.response_slider2.draw()
        
        elif self.phase == self.feedback_phase:
            if hasattr(self, 'response_onset2'):
                # Show yellow feedback marker on slider2
                self.session.response_slider2.marker.inner_color = self.session.settings['slider'].get('feedbackColor')
                self.session.response_slider1.draw()
                self.session.response_slider2.draw()
                self.session.fixation_lines.draw()
            else:
                # Show "Too late!" message when no response made
                self.session.too_late_stimulus.draw()
                self.session.response_slider1.draw()
                self.session.response_slider2.draw()

def main(subject, session, run, slider_type='natural', settings='default', calibrate_eyetracker=False):
    from session import WTPSession
    output_dir, output_str = get_output_dir_str(subject, session, 'estimation_task', run)
    settings_fn, use_eyetracker = get_settings(settings)

    session = WTPSession(output_str=output_str, subject=subject,
                          output_dir=output_dir, settings_file=settings_fn, 
                          run=run, eyetracker_on=use_eyetracker,
                          slider_type=slider_type,
                          calibrate_eyetracker=calibrate_eyetracker)

    session.create_trials()
    session.run()

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('subject', type=str, help='Subject nr')
    argparser.add_argument('session', type=str, help='Session')
    argparser.add_argument('run', type=int, help='Run')
    argparser.add_argument('--settings', type=str, help='Settings label', default='default')
    argparser.add_argument('--calibrate_eyetracker', action='store_true', dest='calibrate_eyetracker')
    argparser.add_argument('--slider_type', type=str, default='natural', help='Response bar type', choices=['natural', 'log', 'two-stage', 'two-sliders'])

    args = argparser.parse_args()

    main(
        args.subject, 
        args.session, 
        args.run, 
        settings=args.settings, 
        slider_type=args.slider_type, 
        calibrate_eyetracker=args.calibrate_eyetracker
    )