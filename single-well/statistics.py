#!python3
import time
import numpy as np
import glob
import matplotlib.pyplot as plt
import os

def make_dir(dir_name):
	"""
	A function that creates a directory dir_name, if it doesn't exist.
	"""
	path = dir_name
	try:
		os.mkdir(path)
	except FileExistsError:
		print(f"Director {path} already exists")
	except OSError:
		print (f"Creation of the directory %s failed" % path)
	else:
		print ("Successfully created the directory %s " % path)

def fourier_spectrum(X, sample_freq=1e-3):
	"""
	Returns the power spectrum (in arbitary units) for a given
	signal X and a sampling frequency sample_freq
	"""
	# find FFT of signal and its amplitude
	ps = np.abs(np.fft.fft(X))**2 
	# store frequencies and indices corresponding to the above FFT
	freqs = np.fft.fftfreq(X.size, sample_freq)
	idx = np.argsort(freqs)

	return (freqs[idx], ps[idx])

def signaltonoise(fs, ps, f_d):
	"""
	Returns the signal to noise ratio in dB for a given range of frequencies
	fs for a powerspectrum ps, specifically for a given frequency
	"""

	# find the index of the specified frequency
	idx = np.where(fs==f_d) 
	# find the value of the spectrum at that frequency
	signal = ps[idx]

	# removing edge cases of when the indices are at the edge
	# of the spectrum
	if idx==0:
		return 0
	elif idx==len(fs):
		return 0

	# calculating noise by averaging/interpolating
	# the neighbouring spectral values from the 
	# specified frequency
	noise = (1/2)*(ps[idx-1] + ps[idx+1])

	return 10*np.log10(signal/noise)


def residence_time(x,flags=1.0):
	"""
	Returns the residence time distribution for a given signal x
	and for a given set of flags (where the timekeeping is triggered)
	"""

	# measure the time between it going between +flag and -flag
	# and add it to an array
	# return the array and/or produce a historgram so it also
	# gives you the distribution
	steps = len(x)

	# keeping track of the crossing indices, * being the null label
	crossing_indices = np.array([(0,"*")])

	tol = 1e-3 # tolerance for when signal crosses the flag

	dt = 1e-3 # took this value from the simulator

	for i in range(steps):
		if x[i] == 0:
			continue
		if (np.abs(x[i]-flags) < tol) and (x[i]-x[i-1] > 0):
			# this is when the signal is breaching the positive crossing
			if len(crossing_indices) > 1:
				# if this isn't the first time a crossing occured
				if crossing_indices[-1][-1] == "-":
					# and if the last crossing was at the other
					# level crossing
					crossing_indices = np.vstack((crossing_indices,[(i,"+")]))
					# append this to the new crossing
			else:
				crossing_indices = np.vstack((crossing_indices,[(i,"+")]))
			# otherwise, ignore completely
		elif (np.abs(x[i]+flags) < tol) and (x[i]-x[i-1] < 0):
			# this is the negative crossing
			if len(crossing_indices) > 1:
				# if this isn't the first time a crossing occured
				if crossing_indices[-1][-1] == "+":
					# and if the last crossing was at the other
					# level crossing
					crossing_indices = np.vstack((crossing_indices,[(i,"-")]))
					# append this to the new crossing
			else:
				crossing_indices = np.vstack((crossing_indices,[(i,"-")]))
			# otherwise, ignore completely


	crossing_indices = crossing_indices[1:] # ignoring the first crossing index since it's (0,*)
	rtseries = np.array([dt*int(i) for i,_ in crossing_indices])

	# setting the first crossing to t=0
	rtseries = rtseries-rtseries[0]

	# finding the distribution by subtracting from an offset timing series
	rtdistribution = rtseries[1:] - rtseries[:-1]

	# returns the indices when the flags were triggered, the timing series and the distribution overall
	return (crossing_indices, rtseries, rtdistribution)


def histogram_movie(data_loc, resolution, plot_loc):
	"""
	A function that returns a directory of images
	depicting the probability density (histogram)
	of the positions for each time step that can be
	made into a movie.
		data_loc : directory where the simulated data is located
		resolution : number of bins for the histogram
		plot_loc : directory where the plots will be placed
	"""

	# making a list of all the files
	file_list = glob.glob(f"{data_loc}/experiment*")
	# importing all of the data from the experiments
	print("Importing data...")
	all_data = np.array([np.load(file) for file in file_list])
	# extracting time series (assumes common time scaling across exps)
	ts = all_data[0][0]
	# extracting all position datadata_lo
	pos_data = np.array([all_data[i][1] for i in range(len(all_data))])

	print("Producing plots...")
	# making histogram plots
	
	# creating a folder to save the plots
	make_dir(plot_loc)

	for i in range(len(ts)):
		print(f"\r{i}/{len(ts)}",end="")
		plt.clf() # clear figure
		plt.xlim(-1.5,1.5) # setting common x axis
		# we are taking the histogram across experiments
		# for each timestep, hence the transposing
		plt.hist(pos_data.T[i],bins=resolution,range=(-1.0,1.0)) # plotting histogram
		plt.title(f"Time : {ts[i]} units") # keeping track of time
		plt.savefig(f"./{plot_loc}/step-{i:05n}.png")
	print("\nPlot production complete!")
	# the plots then can be made into a movie to see the development
	# of the histograms using (requires FFMPEG)
	#	ffmpeg -framerate 24 -i step-%05d.png output.mp4
	

def signal_ensemble(data_loc,resolution,plot_loc):
	"""
	A function that returns heatmap of the position distributions
		data_loc : directory where the simulated data is located
		resolution : number of bins for the histogram
		plot_loc : directory where the plots will be placed
	"""
	# making a list of all the files
	file_list = glob.glob(f"{data_loc}/experiment*")
	# importing all of the data from the experiments
	print("Importing data...")
	all_data = np.array([np.load(file) for file in file_list])
	# extracting time series (assumes common time scaling across exps)
	ts = all_data[0][0]
	# extracting all position datadata_lo
	pos_data = np.array([all_data[i][1] for i in range(len(all_data))])

	print("Producing plots...")
	# making histogram plots
	
	# creating a folder to save the plots
	make_dir(plot_loc)

	ensemble_histogram = np.array([np.histogram(pos_data.T[i], bins=resolution, range=(-1.0,1.0))[0] for i in range(len(ts))])
	# generates a 2D histogram for each time step

	# displaying the histogram
	plt.pcolor(ensemble_histogram.T)
	# relabeling axes
	
	# making the ticks correct
	# firstly, the xticks
	x_t_pos = range(0,1000,100) # we are sticking to just 10 ticks
	x_t_labels = [f"{t:.2f}" for t in ts[::100]] # choosing the right time values
	plt.xticks(x_t_pos, x_t_labels)	
	# now, the yticks
	y_t_pos = range(0,resolution,1)
	y_t_labels = [f"{x:.2f}" for x in np.linspace(-1.0,1.0,resolution)]
	plt.yticks(y_t_pos, y_t_labels)
	plt.xlabel("Time")
	plt.ylabel("Position")
	plt.title("Probability distribution of nanosphere across time")
	plt.show()
	plt.savefig(f"{plot_loc}/plot.png")

	