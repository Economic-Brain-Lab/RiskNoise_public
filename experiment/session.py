from exptools2.core import PylinkEyetrackerSession, Trial
from psychopy import event
from stimuli import ResponseSlider, FixationLines, TextStim, RangeResponseSlider, DiscreteResponseSlider
import yaml
import os.path as op
from instruction import InstructionTrial
from task import TaskTrial, OutroTrial, DummyWaiterTrial, ProbCueTrial, TwoStageTasktrial, TwoSliderTasktrial
import numpy as np
from pathlib import Path

class WTPSession(PylinkEyetrackerSession):
    def __init__(self, output_str, subject=None, output_dir=None, settings_file=None, run=None, eyetracker_on=False, calibrate_eyetracker=False,
                 slider_type='natural'):

        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file, eyetracker_on=eyetracker_on)

        self.show_eyetracker_calibration = calibrate_eyetracker

        self.mouse = event.Mouse(visible=False)

        self.instructions = yaml.safe_load(open(op.join(op.dirname(__file__), 'instruction_texts.yml'), 'r'))

        self.settings['subject'] = subject
        self.settings['run'] = run

        self.fixation_lines = FixationLines(self.win,
                                            self.settings['cloud'].get('aperture_radius'),
                                            color=(1, -1, -1),
                                            **self.settings['fixation_lines'])
        txt_height = self.settings['various'].get('text_height')
        txt_color = self.settings['various'].get('text_color')
        txt_align = 'center'
        self.too_late_stimulus = TextStim(self.win, text='Too late!', pos=(0, 0), color=txt_color, height=txt_height,
                                          alignText=txt_align, anchorHoriz='center')

        self.slider_type = slider_type
        self._setup_response_slider(slider_type=slider_type)

        print("Window colorSpace:", self.win.colorSpace)


    def _setup_response_slider(self, slider_type='natural'):

        position_slider = (0, 0)
        length_line = self.settings['slider'].get('max_length')

        if slider_type in ['natural', 'log']:
            self.response_slider = ResponseSlider(self.win,
                                            position_slider,
                                            length_line,
                                            self.settings['slider'].get('height'),
                                            self.settings['slider'].get('color'),
                                            self.settings['slider'].get('borderColor'),
                                            self.settings['slider'].get('range'),
                                            marker_position=None,
                                            markerColor=self.settings['slider'].get('markerColor'),
                                            borderWidth=self.settings['slider'].get('borderWidth'),
                                            text_height=self.settings['slider'].get('text_height'),
                                            slider_type=slider_type)
        elif slider_type == 'two-stage':

            width_proportion = self.settings['slider'].get('width_proportion', 0.10)

            self.response_slider1 = RangeResponseSlider(self.win,
                                            position_slider,
                                            length_line,
                                            self.settings['slider'].get('height'),
                                            self.settings['slider'].get('color'),
                                            self.settings['slider'].get('borderColor'),
                                            self.settings['slider'].get('range'),
                                            marker_position=None,
                                            markerColor=self.settings['slider'].get('markerColor'),
                                            borderWidth=self.settings['slider'].get('borderWidth'),
                                            text_height=self.settings['slider'].get('text_height'),
                                            slider_type='natural',
                                            width_proportion=width_proportion,
                                            )


            self.response_slider2 = ResponseSlider(self.win,
                                            position_slider,
                                            length_line,
                                            self.settings['slider'].get('height'),
                                            self.settings['slider'].get('color'),
                                            self.settings['slider'].get('borderColor'),
                                            self.settings['slider'].get('range'),
                                            show_number=True,
                                            marker_position=None,
                                            markerColor=self.settings['slider'].get('markerColor'),
                                            borderWidth=self.settings['slider'].get('borderWidth'),
                                            text_height=self.settings['slider'].get('text_height'),
                                            slider_type='natural')

        elif slider_type == 'two-sliders':
            self.response_slider1 = DiscreteResponseSlider(self.win,
                                (0, 2),
                                length_line,
                                self.settings['slider'].get('height'),
                                self.settings['slider'].get('color'),
                                self.settings['slider'].get('borderColor'),
                                self.settings['slider'].get('range'),
                                marker_position=None,
                                markerColor=self.settings['slider'].get('markerColor'),
                                borderWidth=self.settings['slider'].get('borderWidth'),
                                text_height=self.settings['slider'].get('text_height'),
                                slider_type='natural',
                                n_steps=self.settings['slider'].get('n_discrete_steps', 7),
                                )
            


            self.response_slider2 = ResponseSlider(self.win,
                                            (0, -2),
                                            length_line,
                                            self.settings['slider'].get('height'),
                                            self.settings['slider'].get('color'),
                                            self.settings['slider'].get('borderColor'),
                                            self.settings['slider'].get('range'),
                                            show_number=True,
                                            marker_position=None,
                                            markerColor=self.settings['slider'].get('markerColor'),
                                            borderWidth=self.settings['slider'].get('borderWidth'),
                                            text_height=self.settings['slider'].get('text_height'),
                                            slider_type='natural') 


    def run(self):
        """ Runs experiment. """
        if self.eyetracker_on and self.show_eyetracker_calibration:
            self.calibrate_eyetracker()

        self.start_experiment()

        if self.eyetracker_on:
            self.start_recording_eyetracker()
        
        outro = -1 #counter of outro pages
        for trial in self.trials:
            if isinstance(trial, OutroTrial):
                outro += 1
                if outro == 0:
                    # select a random trial
                    self.sampled_trial = np.random.choice([
                        trl for trl in self.trials 
                        # get just experimental trials
                        if isinstance(trl, (TaskTrial, TwoStageTasktrial, TwoSliderTasktrial))
                        # get trials that were responded to
                        and trl.parameters.get('response') != None
                    ])
                    if Path(self.settings_file).stem == 'demo':
                        mssg_bids = '\n'.join(
                            ['Here is the list of lottery tickets and your bids:']
                            + [
                                f'\t{idx_trl + 1}.\tJackpot: {val_trl.parameters["payoff"]} AUD;\tChances: {int(val_trl.parameters["prob"] * 100)}%;\tYour bid: {val_trl.parameters["response"]:.2f} AUD'
                                for idx_trl, val_trl in enumerate([
                                    trl for trl in self.trials
                                    if isinstance(trl, (TaskTrial,TwoStageTasktrial,TwoSliderTasktrial))
                                ])
                            ]
                        )
                    # run a bidding process and lottery draws
                    self.sampled_payoff = self.sampled_trial.parameters['payoff']
                    self.sampled_chance = self.sampled_trial.parameters['prob']
                    self.subject_bid = round(float(self.sampled_trial.parameters['response']), 2)
                    self.computer_bid = round(np.random.uniform(0,self.settings['task'].get('budget')), 2)
                    if self.computer_bid > self.subject_bid:
                        self.lottery_outcome = 0
                        self.subject_prize = 0
                    else:
                        self.lottery_outcome = np.random.choice(
                            [self.sampled_payoff, 0],
                            p = [self.sampled_chance, 1 - self.sampled_chance]
                        )
                        self.subject_prize = round(
                            self.settings['task'].get('budget') 
                            - self.computer_bid
                            + self.lottery_outcome,
                            2
                        )
                    # compile outcomes for saving
                    outcomes = dict(
                        sampled_trial = self.sampled_trial.trial_nr,
                        sampled_payoff = self.sampled_payoff,
                        sampled_prob = self.sampled_chance,
                        subject_bid = self.subject_bid,
                        computer_bid = self.computer_bid,
                        auction_winner = [
                            'subject', 'computer'
                        ][int(self.computer_bid > self.subject_bid)],
                        lottery_outcome = self.lottery_outcome,
                        subject_prize = self.subject_prize
                    )
                    # compile messages about outcomes
                    mssg_ticket = f'You drew a ticket with a jackpot of {self.sampled_payoff} AUD at {int(self.sampled_chance * 100)}% chance of winning.'
                    mssg_sbid = f'For this ticket, your bid was {self.subject_bid:.2f} AUD.'
                    mssg_cbid = f'The computer bid was {self.computer_bid:.2f} AUD.'
                    mssg_auction = [
                        '\n'.join([
                            f'Your bid was higher and you won the auction. Congratulations!', 
                            f'You will only need to pay {self.computer_bid:.2f} AUD for the lottery ticket',
                            f'Your current prize pot is {(self.settings["task"].get("budget") - self.computer_bid):.2f} AUD.',
                            f'We will now proceed to drawing the lottery.'
                        ]),
                        '\n'.join([
                            f'Your bid was lower and you lost the auction.', 
                        ])
                    ][int(self.computer_bid > self.subject_bid)]
                    mssg_lottery = [
                        '\n'.join([
                            f'You won {self.lottery_outcome} AUD on the lottery.', 
                            f'Your total prize is {self.subject_prize:.2f} AUD.',
                            f'Congratulations!'
                        ]),
                        '\n'.join([
                            f'Unfortunately, you will not receive any prize.',
                            f'You will still be compensated for your time.' 
                        ])
                    ][int(self.computer_bid > self.subject_bid)]
                    mssg = '\n'.join([
                        f'This was the last trial.',
                        f'We will now proceed to drawing your lottery ticket.\n\n'
                    ])
                    if Path(self.settings_file).stem == 'demo':
                        mssg += mssg_bids
                if outro == 1:
                   mssg = '\n'.join([
                        mssg_ticket,
                        mssg_sbid,
                        f'We will now proceed to drawing computer bid.'
                    ])
                if outro == 2:
                    mssg = '\n'.join([
                        mssg_ticket,
                        mssg_sbid,
                        mssg_cbid,
                        mssg_auction
                    ])
                if outro == 3:
                    mssg = '\n'.join([
                        mssg_lottery,
                        'Thank you for your participation.',
                        'Please remain as you are. Somebody will assist you shortly.'
                    ])
                
                trial.set_text(mssg)
                
                mssg_bottom = 'Press LEFT mouse button to continue.'
                if outro == 3:
                    mssg_bottom = ''
                trial.set_bottom_text(mssg_bottom)

            trial.run()
        
        # save bidding and lottery outcome data
        outcomes_file = op.join(self.output_dir, self.output_str + "_outcomes.yml")
        with open(outcomes_file, "w") as f_out:
            yaml.dump(outcomes, f_out, indent=4, default_flow_style=False)

        self.close()

    def create_trials(self, include_instructions=True):
        """Create trials."""

        instruction_trials_list = [
            # InstructionTrial(self, 0, self.instructions['instruction1'].format(run=self.settings['run']))
            InstructionTrial(self, 0, pg_txt, bottom_txt='Press LEFT button to continue.')
            for pg_txt in self.instructions['instruction1']
        ]
        dummy_trial = DummyWaiterTrial(self, 0, n_triggers=self.settings['mri']['n_dummy_scans'])
        
        self.trials = instruction_trials_list + [dummy_trial]

        if not include_instructions:
            self.trials = self.trials[1:]

        # n_trials = self.settings['task'].get('n_trials')
        n_reps = self.settings['task'].get('n_reps')
        n_runs = self.settings['task'].get('n_runs')
        n_probs = len(self.settings['task'].get('probabilities'))
        n_payoffs = len(self.settings['task']['payoffs'])
        n_trials = n_probs * n_payoffs * n_reps * n_runs

        # # Make sure n_trials is a multiple of 6 and 4 (or throw error)
        # if n_trials % n_probs != 0:
        #     raise ValueError('n_trials should be a multiple of n_probs')
        # if n_trials % n_payoffs != 0:
        #     raise ValueError('n_trials should be a multiple of n_payoffs')

        probs = list(self.settings['task']['probabilities'])
        # np.random.shuffle(probs)

        probs_ = probs * n_reps
        payoffs_ = list(self.settings['task']['payoffs'])

        trial_nr = 1

        possible_isis = self.settings['durations'].get('isi')
        isis = possible_isis * int(np.ceil(n_trials / len(possible_isis)))
        isis = isis[:n_trials]
        
        # Handle ITI (inter-trial interval) similarly to ISI
        possible_itis = self.settings['durations'].get('iti', [0.0])  # Default to [0.0] if not specified
        if not isinstance(possible_itis, list):
            possible_itis = [possible_itis]  # Convert single value to list
        itis = possible_itis * int(np.ceil(n_trials / len(possible_itis)))
        itis = itis[:n_trials]

        for run in range(n_runs):
            np.random.shuffle(probs_)
            for prob in probs_:
                # probTrl = ProbCueTrial(self, -1, prob)
                # probTrl.text.text = ''
                # self.trials.append(probTrl)

                np.random.shuffle(payoffs_)
                for payoff in payoffs_:
                    
                    if self.slider_type == 'two-stage':
                        self.trials.append(TwoStageTasktrial(self, trial_nr, jitter=isis[trial_nr-1], 
                                                iti=itis[trial_nr-1], payoff=payoff, prob=prob))

                    elif self.slider_type == 'two-sliders':
                        self.trials.append(TwoSliderTasktrial(self, trial_nr, jitter=isis[trial_nr-1],
                                                iti=itis[trial_nr-1], payoff=payoff, prob=prob))
                    else:
                        self.trials.append(TaskTrial(self, trial_nr, jitter=isis[trial_nr-1], 
                                                iti=itis[trial_nr-1], payoff=payoff, prob=prob))
                    trial_nr += 1
            if run < (n_runs - 1):
                blk_break = InstructionTrial(
                    self, 0, 
                    f'This was run {run + 1}. Take a short break.', 
                    bottom_txt='Press LEFT button to continue.')
                blk_break.text.alignText = 'center'
                blk_break.text2.alignText = 'center'
                self.trials.append(blk_break)


        # append different outro pages to serve for lottery drawing
        n_pages = 4
        for pg in range(n_pages):
            otrl = OutroTrial(session=self)
            otrl.text.alignText = 'center'
            otrl.text2.alignText = 'center'
            self.trials.append(otrl)
