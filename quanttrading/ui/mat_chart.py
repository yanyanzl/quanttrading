

import matplotlib as mp
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import ConciseDateFormatter
from matplotlib.colors import LogNorm
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
from datetime import datetime as dt
from event import Event, EventEngine
from constant import EVENT_PLOT
from datatypes import PlotData
# import mplfinance as mf


x = np.linspace(0, 2, 100)  # Sample data.

data1, data2, data3, data4 = np.random.randn(4, 100)


class DataPlot():

    def __init__(self, eventEngine:EventEngine, dataSize:int = 500):
        self.eventEngine = eventEngine
        self.size = dataSize
        self.ani = None
        self.ax:Axes = None
        self.fig: Figure = None

        self.line: Line2D = None
        # date = dt.now().strftime("%H:%M:%S.%f")
        date = " "
        self.origin_data_x: np.ndarray = np.array([date for _ in range(dataSize)], dtype=object)

        print(f"{self.origin_data_x}")
        self.origin_data_y: np.ndarray = np.zeros((dataSize),dtype= float)

        self.count:int = 0
        self.inited:bool = False
        self.x_data:list = []
        self.y_data:list = []
        self.x_tick:list = []

        self.added_num:int = 0

        self.register_event()
        self.func_animation_draw()
        del date

    def register_event(self) -> None:
        """ register event to listen on"""
        self.eventEngine.register(EVENT_PLOT, self.process_plot_event)
    
    def process_plot_event(self, event:Event) -> None:
        """ process the plot event """
        if event:
            data:PlotData = event.data
            # print(f"receiving data {data=}")
            if self.inited:
                self.origin_data_x[:-1] = self.origin_data_x[1:]
                self.origin_data_y[:-1] = self.origin_data_y[1:]

                self.origin_data_x[-1] = data['x_data']
                self.origin_data_y[-1] = data['y_data']

                self.added_num += 1
            else:
                self.origin_data_x[self.count] = data['x_data']
                self.origin_data_y[self.count] = data['y_data']
            
            self.count += 1
            if self.count == self.size:
                self.inited = True
            # print(f"leaving data {data=}")

    def update_data(self,frame) -> list:
        """ """
        # print(f".......... 1")
        if frame < self.size:
            if self.origin_data_y[frame]:
                self.x_data.append(self.origin_data_x[frame])
                self.y_data.append(self.origin_data_y[frame])
                # self.x_tick.append(frame)
                
        elif frame == self.size:
            if self.added_num > 0:
                offset = - self.added_num
                self.x_data.append(self.origin_data_x[offset])
                self.y_data.append(self.origin_data_y[offset])

                self.added_num -= 1
        if len(self.x_data) > self.size:
            self.x_data = self.x_data[-self.size:]
            self.y_data = self.y_data[-self.size:]

        # print(f".......... 2 {self.origin_data_x=}")
        # plt.xticks(range(0,len(self.x_data)), self.x_data)
        # self.ax.set_xticks(self.x_data)
        # ticks = [t for t in range(0,self.size)]
        # self.ax.get_xticks()
        # self.ax.set_xticks(ticks, self.origin_data_x)

        self.x_tick = [x for x in range(0, len(self.x_data))]
        self.line.set_data(self.x_tick, self.y_data)

        # self.ax.set_ylim(float(self.origin_data_y.min())-1, self.origin_data_y.max()+1)
        return (self.line, self.ax.xaxis, self.ax.yaxis)

    def func_animation_draw(self) -> None:
        """
        The FuncAnimation class allows us to create an animation by passing
        a function that iteratively modifies the data of a plot.
        A usual FuncAnimation object takes a Figure that we want to animate
        and a function func that modifies the data plotted on the figure.
            It uses the frames parameter to determine the length of the 
            animation. The interval parameter is used to determine time 
            in milliseconds between drawing of two frames. Animating using 
            FuncAnimation typically requires these steps:

        Plot the initial figure as you would in a static plot. Save all
        the created artists, which are returned by the plot functions,
            in variables so that you can access and modify them later 
            in the animation function.
        Create an animation function that updates the artists for a given
        frame. Typically, this calls set_* methods of the artists.

        Create a FuncAnimation, passing the Figure and the animation function.

        Save or show the animation using one of the following methods:
            pyplot.show to show the animation in a window
            Animation.to_html5_video to create a HTML <video> tag
            Animation.to_jshtml to create HTML code with 
            interactive JavaScript animation controls
            Animation.save to save the animation to a file
        """
        style.use('fivethirtyeight')
        self.fig, self.ax = plt.subplots(figsize=(10,10))
        
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.20)

        self.line = self.ax.plot([], [], label=f'realRange')[0]
        # plt.xticks(range(0,len(self.x_data)), self.x_data)
        # self.ani = animation.FuncAnimation(fig=fig, func=self.update_data, frames=30, interval=30, blit = True)
        self.ani = animation.FuncAnimation(fig=self.fig, func=self.update_data, frames=30, init_func=self.init_ax, interval=10, blit = True, save_count=self.size)
        # plt.xticks(range(0,len(self.x_data)), self.x_data)
        plt.show()

    def init_ax(self) -> list:
        # self.ax.set(xlim=[0, 100], ylim=[-10, 10], xlabel='Time [s]', ylabel='Range')
        self.ax.set(xlim=[0, self.size],ylim=[0, 10], xlabel='Time [s]', ylabel='Range')

        # A FuncFormatter is created automatically.
        self.ax.xaxis.set_major_formatter(self.format_fn)
        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax.legend()
        return self.line,

    def format_fn(self, tick_val, tick_pos):
        index = int(tick_val)
        if  index < self.size and self.origin_data_x[index]:
            return self.origin_data_x[index]
        else:
            return ''

def multi_plot() -> None:

    # Note that even in the OO-style, we use `.pyplot.figure` to create the Figure.
    fig, (ax, ax1) = plt.subplots(1,2, figsize=(15, 8.1), layout='constrained')
    ax.plot(x, x, label='linear', color='orange', linewidth=3)  # Plot some data on the Axes.
    ax.plot(x, x**2, label='quadratic')  # Plot more data on the Axes...
    ax.plot(x, x**3, label='cubic')  # ... and some more.
    ax.set_xlabel('x label')  # Add an x-label to the Axes.
    ax.set_ylabel('y label')  # Add a y-label to the Axes.
    ax.set_title("Simple Plot")  # Add a title to the Axes.
    ax.legend()  # Add a legend.


def set_ticks_axes() -> None:
    xdata = np.arange(len(data1))  # make an ordinal for this
    fig, axs = plt.subplots(2, 1, layout='constrained')
    axs[0].plot(xdata, data1)
    axs[0].set_title('Automatic ticks')

    axs[1].plot(xdata, data1)
    axs[1].set_xticks(np.arange(0, 100, 30), ['zero', '30', 'sixty', '90'])
    axs[1].set_yticks([-1.5, 0, 1.5])  # note that we don't need to specify labels
    axs[1].set_title('Manual ticks')

def date_and_string_axes() -> None:
    # dates
    fig, ax = plt.subplots(figsize=(5, 2.7), layout='constrained')
    dates = np.arange(np.datetime64('2021-11-15'), np.datetime64('2021-12-25'),
                    np.timedelta64(1, 'h'))
    data = np.cumsum(np.random.randn(len(dates)))
    ax.plot(dates, data)
    ax.xaxis.set_major_formatter(ConciseDateFormatter(ax.xaxis.get_major_locator()))

    # string
    fig, ax = plt.subplots(figsize=(5, 2.7), layout='constrained')
    categories = ['turnips', 'rutabaga', 'cucumber', 'pumpkins']
    ax.bar(categories, np.random.rand(len(categories)))

def color_map() -> None:
    """
    Often we want to have a third dimension in a plot represented by colors
    in a colormap. Matplotlib has a number of plot types that do this:
    """

    X, Y = np.meshgrid(np.linspace(-3, 3, 128), np.linspace(-3, 3, 128))
    Z = (1 - X/2 + X**5 + Y**3) * np.exp(-X**2 - Y**2)

    fig, axs = plt.subplots(2, 2, layout='constrained')
    pc = axs[0, 0].pcolormesh(X, Y, Z, vmin=-1, vmax=1, cmap='RdBu_r')
    fig.colorbar(pc, ax=axs[0, 0])
    axs[0, 0].set_title('pcolormesh()')

    co = axs[0, 1].contourf(X, Y, Z, levels=np.linspace(-1.25, 1.25, 11))
    fig.colorbar(co, ax=axs[0, 1])
    axs[0, 1].set_title('contourf()')

    pc = axs[1, 0].imshow(Z**2 * 100, cmap='plasma', norm=LogNorm(vmin=0.01, vmax=100))
    fig.colorbar(pc, ax=axs[1, 0], extend='both')
    axs[1, 0].set_title('imshow() with LogNorm()')

    pc = axs[1, 1].scatter(data1, data2, c=data3, cmap='RdBu_r')
    fig.colorbar(pc, ax=axs[1, 1], extend='both')
    axs[1, 1].set_title('scatter()')

"""
The animation process in Matplotlib can be thought of in 2 different ways:

FuncAnimation: Generate data for first frame and then modify this data
 for each frame to create an animated plot.
ArtistAnimation: Generate a list (iterable) of artists that will draw
 in each frame in the animation.
FuncAnimation is more efficient in terms of speed and memory as it draws
 an artist once and then modifies it. On the other hand ArtistAnimation
   is flexible as it allows any iterable of artists to be animated in a
     sequence.

"""
def func_animation_draw() -> None:
    """
    The FuncAnimation class allows us to create an animation by passing
      a function that iteratively modifies the data of a plot.
    A usual FuncAnimation object takes a Figure that we want to animate
      and a function func that modifies the data plotted on the figure.
        It uses the frames parameter to determine the length of the 
        animation. The interval parameter is used to determine time 
        in milliseconds between drawing of two frames. Animating using 
        FuncAnimation typically requires these steps:

    Plot the initial figure as you would in a static plot. Save all
      the created artists, which are returned by the plot functions,
        in variables so that you can access and modify them later 
        in the animation function.
    Create an animation function that updates the artists for a given
      frame. Typically, this calls set_* methods of the artists.

    Create a FuncAnimation, passing the Figure and the animation function.

    Save or show the animation using one of the following methods:
        pyplot.show to show the animation in a window
        Animation.to_html5_video to create a HTML <video> tag
        Animation.to_jshtml to create HTML code with 
        interactive JavaScript animation controls
        Animation.save to save the animation to a file
    """
    fig, ax = plt.subplots()
    line = ax.plot([],[])
    
    t = np.linspace(0, 3, 40)
    g = -9.81
    v0 = 12
    z = g * t**2 / 2 + v0 * t

    v02 = 5
    z2 = g * t**2 / 2 + v02 * t

    scat = ax.scatter(t[0], z[0], c="b", s=5, label=f'v0 = {v0} m/s')
    line2 = ax.plot(t[0], z2[0], label=f'v0 = {v02} m/s')[0]
    ax.set(xlim=[0, 3], ylim=[-4, 10], xlabel='Time [s]', ylabel='Z [m]')
    ax.legend()


    def update(frame):
        # for each frame, update the data stored on each artist.
        x = t[:frame]
        y = z[:frame]
        # update the scatter plot:
        data = np.stack([x, y]).T
        scat.set_offsets(data)
        # update the line plot:
        line2.set_xdata(t[:frame])
        line2.set_ydata(z2[:frame])
        return (scat, line2)


    ani = animation.FuncAnimation(fig=fig, func=update, frames=40, interval=30)

    # ani.save(filename="pillow_example.gif", writer="pillow")
    # ani.save(filename="pillow_example.apng", writer="pillow")
    # ani.save(filename="html_example.html", writer="html")
    # ani.save(filename="html_example.htm", writer="html")
    
    plt.show()

def artist_animation_draw() -> None:
    """
    ArtistAnimation can be used to generate animations if there is data
    stored on various different artists. This list of artists is then 
    converted frame by frame into an animation. For example, when we 
    use Axes.barh to plot a bar-chart, it creates a number of artists 
    for each of the bar and error bars. To update the plot, one would 
    need to update each of the bars from the container individually and
    redraw them. Instead, animation.ArtistAnimation can be used to plot
        each frame individually and then stitched together to form an 
        animation. A barchart race is a simple example for this.
    """
    fig, ax = plt.subplots()
    rng = np.random.default_rng(19680801)
    data = np.array([20, 20, 20, 20])
    x = np.array([1, 2, 3, 4])

    artists = []
    colors = ['tab:blue', 'tab:red', 'tab:green', 'tab:purple']
    for i in range(20):
        data += rng.integers(low=0, high=10, size=data.shape)
        container = ax.barh(x, data, color=colors)
        artists.append(container)


    ani = animation.ArtistAnimation(fig=fig, artists=artists, interval=400)
    plt.show()

# func_animation_draw()
# artist_animation_draw()


def save_animations() -> None:
    """
    To save animations using any of the writers, we can use the 
    animation.Animation.save method. It takes the filename that we want to
    save the animation as and the writer, which is either a string or a 
    writer object. It also takes an fps argument. This argument is different
    than the interval argument that FuncAnimation or ArtistAnimation uses. 
    fps determines the frame rate that the saved animation uses, whereas 
    interval determines the frame rate that the displayed animation uses.

    """

# plt.show()