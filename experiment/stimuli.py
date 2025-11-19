from psychopy.visual import Circle, Line, Rect, TextStim, Pie
import numpy as np

range_ = range

class FixationLines(object):

    def __init__(self, win, circle_radius, color, center_fixation_size=0.25, plus_sign=False, draw_circle=True, draw_outer_cross=True, *args, **kwargs):

        # Get window size in the window's units (deg if window units='deg')
        if hasattr(win, 'units') and win.units == 'deg':
            # Calculate window size in degrees
            monitor = win.monitor
            width_deg = 2 * np.degrees(np.arctan(monitor.getWidth() / (2.0 * monitor.getDistance())))
            height_deg = width_deg * (win.size[1] / win.size[0])  # maintain aspect ratio
            win_size = np.array([width_deg, height_deg])
        else:
            win_size = win.size
            
        max_dimension = np.max(win_size)

        kwargs['colorSpace'] = 'rgb'

        coord = circle_radius * 1.1 * np.cos(np.pi / 4)

        # Fixation cross center
        self.line1 = Line(win, start=(-center_fixation_size, -center_fixation_size),
                          end=(center_fixation_size, center_fixation_size), lineColor=color, *args, **kwargs)
        
        self.line2 = Line(win, start=(-center_fixation_size, center_fixation_size),
                            end=(center_fixation_size, -center_fixation_size), lineColor=color, *args, **kwargs)

        self.fixation_cross = [self.line1, self.line2]

        self.elements = []

        if draw_outer_cross:
            self.line3 = Line(win, start=(-coord, -coord),
                            end=(-max_dimension, -max_dimension), lineColor=color, *args, **kwargs)

            self.line4 = Line(win, start=(coord, coord),
                            end=(max_dimension, max_dimension), lineColor=color, *args, **kwargs)

            self.line5 = Line(win, start=(-coord, coord),
                            end=(-max_dimension, max_dimension), lineColor=color, *args, **kwargs)

            self.line6 = Line(win, start=(coord, -coord),
                                end=(max_dimension, -max_dimension), lineColor=color, *args, **kwargs)


            self.elements += [self.line3, self.line4, self.line5, self.line6]

        if draw_circle:
            self.aperture = Circle(win, radius=circle_radius * 1.1, fillColor=(0, 0, 0), lineColor=color, lineWidth=kwargs['lineWidth'])
            self.elements.append(self.aperture)


    def draw(self, draw_fixation_cross=True):

        
        if draw_fixation_cross:
            for line in self.fixation_cross:
                line.draw()

        for line in self.elements:
            line.draw()

    def setColor(self, color, fixation_cross_only=False):

        for line in self.fixation_cross:
            line.lineColor = color

        if not fixation_cross_only:
            for line in self.elements:
                line.lineColor = color

class RoundedRectangle(object):

    def __init__(self, win, pos, width, height, corner_radius, color):

        x, y = pos

        self.width = width
        self.height = height
        self.corner_radius = corner_radius

        self.border_corners = [
            Circle(win, radius=corner_radius, pos=[x - width/2 + corner_radius, y + height/2 - corner_radius], fillColor=color),
            Circle(win, radius=corner_radius, pos=[x + width/2 - corner_radius, y + height/2 - corner_radius], fillColor=color),
            Circle(win, radius=corner_radius, pos=[x - width/2 + corner_radius, y - height/2 + corner_radius], fillColor=color),
            Circle(win, radius=corner_radius, pos=[x + width/2 - corner_radius, y - height/2 + corner_radius], fillColor=color)
        ]

        self.border_sides = [
            Rect(win, width=width-2*corner_radius, height=corner_radius*2, pos=[x, y - height/2 + corner_radius], fillColor=color,),
            Rect(win, width=width-2*corner_radius, height=corner_radius*2, pos=[x, y + height/2 - corner_radius], fillColor=color,),
            Rect(win, width=corner_radius*2, height=height-2*corner_radius, pos=[x - width/2 + corner_radius, y], fillColor=color,),
            Rect(win, width=corner_radius*2, height=height-2*corner_radius, pos=[x + width/2 - corner_radius, y], fillColor=color,)
        ]

        self.inner_rectangle = Rect(win, width=width-2*corner_radius, height=height-2*corner_radius, pos=[x, y], fillColor=color)
        self.color = color

    def draw(self):
        for shape in self.border_corners + self.border_sides:
            shape.draw()
        self.inner_rectangle.draw()
    
    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        self.update_position()

    def update_position(self):

        x, y = self._pos

        self.border_corners[0].pos = [x - self.width/2 + self.corner_radius, y + self.height/2 - self.corner_radius]
        self.border_corners[1].pos = [x + self.width/2 - self.corner_radius, y + self.height/2 - self.corner_radius]
        self.border_corners[2].pos = [x - self.width/2 + self.corner_radius, y - self.height/2 + self.corner_radius]
        self.border_corners[3].pos = [x + self.width/2 - self.corner_radius, y - self.height/2 + self.corner_radius]

        self.border_sides[0].pos = [x, y - self.height/2 + self.corner_radius]
        self.border_sides[1].pos = [x, y + self.height/2 - self.corner_radius]
        self.border_sides[2].pos = [x - self.width/2 + self.corner_radius, y]
        self.border_sides[3].pos = [x + self.width/2 - self.corner_radius, y]

        self.inner_rectangle.pos = [x, y]
        self.inner_rectangle.pos = [x, y]

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        for shape in self.border_corners + self.border_sides + [self.inner_rectangle]:
            shape.fillColor = value

        self._color = value


class RoundedRectangleWithBorder(object):

    def __init__(self, win, pos, width, height, corner_radius, inner_color, outer_color, borderWidth=0.05):
        adjusted_corner_radius = corner_radius - borderWidth
        self.outer_rectangle = RoundedRectangle(win, pos, width, height, corner_radius, outer_color)
        self.inner_rectangle = RoundedRectangle(win, pos, width-borderWidth*2, height-borderWidth*2, adjusted_corner_radius, inner_color)
        self.width = width

    def draw(self):
        self.outer_rectangle.draw()
        self.inner_rectangle.draw()

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        self.update_position()

    def update_position(self):
        self.outer_rectangle.pos = self._pos
        self.inner_rectangle.pos = self._pos

    # Make a property 'inner_color' that sets the color of the inner rectangle
    @property
    def inner_color(self):
        return self.inner_rectangle.color
    
    @inner_color.setter
    def inner_color(self, value):
        self.inner_rectangle.color = value


class ResponseSlider(object):

    def __init__(self, win, position, length, height, color, borderColor, range, marker_position, show_marker=False,
                 show_number=True,
                 markerColor=None,
                 text_height=0.5,
                 slider_type='natural',
                 slider_width=None,
                 borderWidth=0.05,
                 *args, **kwargs):

        assert slider_type in ['natural', 'log']
        self.range = range
        self.height = height

        self.slider_type = slider_type
        self.show_number = show_number

        if self.show_number:
            self.number = TextStim(win, text='0', pos=(position[0], position[1] - height*1.5), color=(1, 1, 1), units='deg', height=text_height)

        if marker_position is None:
            marker_position = np.random.randint(range[0], range[1]+1) 
       
        if markerColor is None:
            markerColor = color

        self.show_marker = show_marker

        self.bar = Rect(win, width=length, height=height, pos=position,
                        lineColor=borderColor, color=color, lineWidth=borderWidth)

        if slider_width is None:
            self.slider_width = height*.5
        else:
            self.slider_width = slider_width

        self.marker = RoundedRectangleWithBorder(win, position, self.slider_width, height*1.5, height*.15, markerColor, borderColor, borderWidth=borderWidth)

        self.setMarkerPosition(marker_position)


    def draw(self):
        self.bar.draw()

        if self.show_marker:
            self.marker.draw()

            if self.show_number:
                if self.slider_type == 'natural':
                    self.number.text = f'${self.marker_position:.2f}'
                elif self.slider_type == 'log':
                    self.number.text = f'${self.marker_position:.2f}'
                self.number.draw()

    def setMarkerPosition(self, number):
        # Clip the number to stay within the valid range
        number = np.clip(number, self.range[0], self.range[1])

        if self.slider_type in ['natural', 'two-stage']:
            # Linear mapping
            fraction = (number - self.range[0]) / (self.range[1] - self.range[0])
            width_bar_minus_marker = self.bar.width - self.marker.width
            position_x = self.bar.pos[0] + fraction * width_bar_minus_marker - width_bar_minus_marker / 2.

        elif self.slider_type == 'log':
            # Logarithmic mapping
            log_min = np.log10(self.range[0])
            log_max = np.log10(self.range[1])
            log_value = (np.log10(number) - log_min) / (log_max - log_min)
            position_x = self.bar.pos[0] + log_value * self.bar.width - self.bar.width / 2.


            # Discrete step size
            step_size = (self.range[1] - self.range[0]) / self.n_discrete_steps
            # Round to nearest step

        # Set marker position
        self.marker.pos = (position_x, self.bar.pos[1])
        self.marker_position = number


    def mouseToMarkerPosition(self, mouse_pos):

        if self.slider_type in ['natural', 'two-stage']:
            fraction = (mouse_pos - self.bar.pos[0] + self.bar.width / 2) / self.bar.width
            fraction = np.clip(fraction, 0, 1)  # Ensure it's between 0 and 1
            return self.range[0] + fraction * (self.range[1] - self.range[0])

        elif self.slider_type == 'log':
            # Convert mouse position to a fraction of the slider width
            fraction = (mouse_pos - self.bar.pos[0] + self.bar.width/2) / self.bar.width
            
            # Ensure the fraction is within valid range
            fraction = max(0, min(1, fraction))
            
            # Convert the fraction to a logarithmic scale
            log_min = np.log10(self.range[0])
            log_max = np.log10(self.range[1])
            
            log_value = log_min + fraction * (log_max - log_min)
            
            return 10 ** log_value
        else:
            raise ValueError("Unsupported slider type")


    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        self.update_position()

    def update_position(self):
        self.bar.pos = self._pos
        self.setMarkerPosition(self.marker_position)

        if self.show_number:
            self.number.pos = (self._pos[0], self._pos[1] - self.bar.height*1.75)
class RangeResponseSlider(ResponseSlider):

    def __init__(self, win, position, length, height, color, borderColor, range, marker_position,
                 width_subrange=None,
                 show_marker=False,
                 show_number=True,
                 markerColor=None,
                 text_height=0.5,
                 slider_type='natural',
                 slider_width=None,
                 width_proportion=0.1,
                 *args, **kwargs):
        self.range = range

        if width_subrange is None:
            width_subrange = (range[1] - range[0]) * width_proportion
            self.width_proportion = width_proportion
        else:
            self.width_proportion = width_subrange / length

        slider_width = width_subrange / (range[1] - range[0]) * length

        length_range = range[1] - range[0]

        self.range_ = range

        self.range = [range[0] + self.width_proportion / 2. * length_range, range[1] - self.width_proportion/ 2.* length_range]



        super().__init__(win, position, length, height, color, borderColor, self.range, marker_position, show_marker=show_marker,
                    show_number=show_number,
                    markerColor=markerColor,
                    text_height=text_height,
                    slider_type=slider_type,
                    slider_width=slider_width,
                    *args, **kwargs)

    def draw(self):
        self.bar.draw()

        if self.show_marker:
            self.marker.draw()

            if self.show_number:
                lower_range = self.marker_position - self.width_proportion * (self.range_[1] - self.range_[0]) / 2
                upper_range = self.marker_position + self.width_proportion * (self.range_[1] - self.range_[0]) / 2

                self.number.text = f'${lower_range:.2f} - ${upper_range:.2f}'
                self.number.draw()

class DiscreteResponseSlider(object):

    def __init__(self, win,
                 position,
                 length,
                 height,
                 color,
                 borderColor,
                 range,
                 marker_position,
                 n_steps=6,
                 show_marker=False,
                 markerColor=None,
                 text_height=None,
                 *args, **kwargs):

        self.range = range

        self.n_steps = n_steps
        self.width_proportion = 1. / n_steps
        self.step_size = (self.range[1] - self.range[0]) / n_steps
        self.bins = np.linspace(self.range[0], self.range[1], n_steps + 1)
        self.marker_position = marker_position
        self.show_marker = show_marker
        self.markerColor = markerColor
        
        if text_height is None:
            text_height = height * 0.5

        self.text_height = text_height

        self.slider_type = 'natural'
        self.slider_width = length / n_steps
        self.borderWidth = kwargs.get('borderWidth', 0.15)
        self.borderColor = borderColor
        self.color = color
        self.height = height

        self.bar = Rect(win, width=length, height=height, pos=position, color=color, lineColor=borderColor, lineWidth=self.borderWidth*10)
        self.marker = Rect(win, width=self.slider_width, height=height, pos=position, color=markerColor, lineColor=borderColor, lineWidth=self.borderWidth*10)


        self.text_stimuli = []

        for i in range_(len(self.bins)):
            text = TextStim(win,
                            text=f'${self.bins[i]:.2f}',
                            pos=(position[0] + (i) * self.slider_width - length / 2.,
                                 position[1] + self.height * .5 + self.text_height), color=(1, 1, 1), units='deg',
                                 height=self.text_height)

            self.text_stimuli.append(text)


    def draw(self):
        self.bar.draw()

        if self.show_marker:
            self.marker.draw()

        for stimulus in self.text_stimuli:
            stimulus.draw()

    def update_marker_position(self, number):
        number = np.clip(number, self.range[0], self.range[1])
        closest_bin = np.digitize(number, self.bins) - 1
        self.marker_position = self.bins[closest_bin]
        self.marker.pos = (self.bar.pos[0] + (closest_bin + 0.5) * self.slider_width - self.bar.width / 2., self.bar.pos[1])
        self.marker.fillColor = self.markerColor
        self.marker.lineColor = self.borderColor
        self.marker.lineWidth = self.borderWidth
        self.marker.draw()

    def setMarkerPosition(self, number):
        self.update_marker_position(number)

    def mouseToMarkerPosition(self, mouse_pos):
        fraction = (mouse_pos - self.bar.pos[0] + self.bar.width / 2) / self.bar.width
        fraction = np.clip(fraction, 0, 1 - 1e-6)
        number = self.range[0] + fraction * (self.range[1] - self.range[0])
        self.update_marker_position(number)
        return self.marker_position

class ProbabilityPieChart(object):

    def __init__(self, window, prob, size, prefix='',
                include_text=True,
                 pos=(0.0, 0.0), color_pos=(.65, .65, .65), color_neg=(-.65, -.65, -.65)):

        deg = prob * 360.

        self.piechart_pos = Pie(window, end=deg, fillColor=color_pos,
                                pos=pos,
                                size=size)
        self.piechart_neg = Pie(window, start=deg, end=360, fillColor=color_neg,
                                pos=pos,
                                size=size)


        self.include_text = include_text

        if self.include_text:
            txt = f'{prefix}{int(prob*100):d}%'
            self.text = TextStim(window, pos=(pos[0], pos[1]+size*1.),
                                text=txt, wrapWidth=size*3, height=size*.75)

    def draw(self):
        self.piechart_pos.draw()
        self.piechart_neg.draw()
        
        if self.include_text:
            self.text.draw()
