"""Python translation of MeasureThePowerOfASignalExample.m.

This script reproduces the MATLAB example that estimates signal power,
occupied bandwidth, and harmonic distortion characteristics for a noisy
chirp and for the output of a nonlinear amplifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np
from scipy.signal import chirp as chirp_signal
from scipy.signal import periodogram


DB_FLOOR_DB = -120.0
THD_KAISER_BETA = 38.0


def rms(signal: np.ndarray) -> float:
	"""Return the root mean square value of the input signal."""

	signal = np.asarray(signal)
	return float(np.sqrt(np.mean(np.square(np.abs(signal)))))


def pow2db(power: np.ndarray | float) -> np.ndarray:
	"""Convert a linear power quantity into decibels."""

	power_arr = np.asarray(power, dtype=float)
	reference = np.finfo(float).tiny
	return np.asarray(10.0 * np.log10(np.maximum(power_arr, reference)))


def bandpower(
	signal: np.ndarray,
	fs: float,
	band: Tuple[float, float] | None = None,
	window: str = "boxcar",
) -> float:
	"""Estimate average power of *signal* within *band* using a periodogram."""

	signal = np.asarray(signal)
	freqs, psd = periodogram(
		signal,
		fs=fs,
		window=window,
		nfft=None,
		return_onesided=True,
		scaling="density",
	)

	if band is None:
		band = (0.0, fs / 2.0)

	f_low, f_high = band
	mask = (freqs >= f_low) & (freqs <= f_high)
	if not np.any(mask):
		return 0.0

	return float(np.trapz(psd[mask], freqs[mask]))


@dataclass
class OccupiedBandwidth:
	width: float
	f_low: float
	f_high: float
	power: float


def occupied_bandwidth(
	signal: np.ndarray,
	fs: float,
	occupancy: float = 0.99,
	freq_limits: Tuple[float, float] | None = None,
	window: str = "boxcar",
	*,
	plot: bool = False,
	ax: Axes | None = None,
) -> OccupiedBandwidth:
	"""Replicate MATLAB's OBW measurement for a 1-D real signal."""

	# This mirrors MATLAB's obw.m logic: always estimate the PSD with a
	# rectangular window, integrate with a rectangular (Riemann) sum, allow
	# optional frequency limits, and convert the requested power percentage
	# into the (100±P)/2 crossings before interpolating Flo and Fhi. The plot
	# annotation matches obw.m, including the occupied-band label and the
	# computed percentage.

	signal = np.asarray(signal)
	if signal.ndim != 1:
		raise ValueError("occupied_bandwidth expects a 1-D signal array")

	freqs, psd = periodogram(
		signal,
		fs=fs,
		window=window,
		return_onesided=True,
		scaling="density",
	)

	if len(freqs) < 2:
		edge = float(freqs[0]) if len(freqs) else 0.0
		return OccupiedBandwidth(0.0, edge, edge, 0.0)

	if freq_limits is None:
		f_min, f_max = float(freqs[0]), float(freqs[-1])
	else:
		f_min, f_max = map(float, freq_limits)
		if f_min >= f_max:
			raise ValueError("freq_limits must satisfy f_min < f_max")

	mask = (freqs >= f_min) & (freqs <= f_max)
	if not np.any(mask):
		return OccupiedBandwidth(0.0, f_min, f_max, 0.0)

	freqs_roi = freqs[mask]
	psd_roi = psd[mask]

	df = np.diff(freqs_roi).mean() if len(freqs_roi) > 1 else fs / len(freqs_roi)
	segment_power = psd_roi * df
	cumulative_power = np.cumsum(segment_power)
	total_power = cumulative_power[-1]
	if total_power <= 0.0:
		return OccupiedBandwidth(0.0, f_min, f_max, 0.0)

	occ_fraction = occupancy / 100.0 if occupancy > 1.0 else occupancy
	occ_fraction = float(np.clip(occ_fraction, 0.0, 1.0))

	lower_target = total_power * (1.0 - occ_fraction) / 2.0
	upper_target = total_power * (1.0 + occ_fraction) / 2.0

	def interpolate_frequency(target_power: float) -> float:
		if target_power <= 0.0:
			return float(freqs_roi[0])
		idx = int(np.searchsorted(cumulative_power, target_power))
		idx = min(max(idx, 1), len(freqs_roi) - 1)
		p0, p1 = cumulative_power[idx - 1], cumulative_power[idx]
		f0, f1 = freqs_roi[idx - 1], freqs_roi[idx]
		if p1 == p0:
			return float(f0)
		return float(f0 + (target_power - p0) * (f1 - f0) / (p1 - p0))

	f_low = interpolate_frequency(lower_target)
	f_high = interpolate_frequency(upper_target)
	bandwidth = f_high - f_low
	power_in_band = upper_target - lower_target

	if plot:
		if ax is None:
			_, ax = plt.subplots()
		assert ax is not None
		psd_db = np.clip(pow2db(psd), DB_FLOOR_DB, None)
		ax.plot(freqs, psd_db, label="Periodogram")
		band_mask = ((freqs >= f_low) & (freqs <= f_high)).tolist()
		ax.fill_between(
			freqs,
			psd_db,
			DB_FLOOR_DB,
			where=band_mask,
			alpha=0.3,
			label=f"Occupied {occ_fraction * 100:.0f}%",
		)
		ax.axvline(f_low, color="tab:red", linestyle="--", linewidth=1.0)
		ax.axvline(f_high, color="tab:red", linestyle="--", linewidth=1.0)
		ax.set_xlabel("Frequency (Hz)")
		ax.set_ylabel("Power/Frequency (dB/Hz)")
		ax.set_title(f"{occ_fraction * 100:.0f}% Occupied Bandwidth: {bandwidth:.3f} Hz")
		ax.set_ylim(DB_FLOOR_DB, np.ceil(psd_db.max() / 5.0) * 5.0)
		ax.legend()
		ax.grid(True, which="both", linestyle=":")

	return OccupiedBandwidth(bandwidth, f_low, f_high, power_in_band)


def plot_thd(
	signal: np.ndarray,
	fs: float,
	*,
	fundamental: float | None = None,
	harmonics: int = 6,
	ax: Axes | None = None,
) -> None:
	"""Replicate MATLAB's thd.m visualization with harmonic annotations."""

	signal = np.asarray(signal, dtype=float)
	if signal.ndim != 1:
		raise ValueError("plot_thd expects a 1-D signal array")

	signal = signal - np.mean(signal)
	n = signal.size
	if n == 0:
		raise ValueError("plot_thd requires a non-empty signal")

	window = np.kaiser(n, THD_KAISER_BETA)
	windowed_signal = signal * window
	freqs, psd = periodogram(
		windowed_signal,
		fs=fs,
		window="boxcar",
		nfft=n,
		detrend='constant',
		return_onesided=True,
		scaling="density",
	)

	if len(freqs) < 2:
		raise ValueError("plot_thd requires at least two frequency bins")

	rbw = fs * np.sum(window**2) / (np.sum(window) ** 2)
	psd_power = psd * rbw
	psd_db = np.clip(pow2db(psd_power), DB_FLOOR_DB, None)
	freqs_khz = freqs / 1000.0

	if fundamental is None:
		fund_idx = int(np.argmax(psd[1:]) + 1) if len(psd) > 1 else 0
		fundamental = float(freqs[fund_idx]) if fund_idx > 0 else 0.0
	else:
		fund_idx = int(np.argmin(np.abs(freqs - fundamental)))
		fundamental = float(freqs[fund_idx])

	if fundamental <= 0.0:
		raise ValueError("Unable to determine the fundamental frequency")

	harmonic_data = []
	for order in range(1, harmonics + 1):
		freq_target = order * fundamental
		if freq_target > fs / 2:
			break
		idx = int(np.argmin(np.abs(freqs - freq_target)))
		harmonic_data.append(
			{
				"order": order,
				"freq": float(freqs[idx]),
				"power": float(psd_power[idx]),
				"power_db": float(psd_db[idx]),
			}
		)

	if not harmonic_data:
		raise ValueError("No harmonics found within Nyquist range")

	fund_power = harmonic_data[0]["power"]
	harm_sum = sum(h["power"] for h in harmonic_data[1:])
	thd_db = -np.inf if harm_sum <= 0.0 or fund_power <= 0.0 else 10.0 * np.log10(harm_sum / fund_power)
	have_harmonics = len(harmonic_data) > 1

	if ax is None:
		_, ax = plt.subplots()
	assert ax is not None

	dc_noise_line, = ax.plot(freqs_khz, psd_db, color="tab:blue", label="DC and Noise")
	ax.set_xlim(0, fs / 2000.0)
	ax.set_xlabel("Frequency (kHz)")
	ax.set_ylabel("Power (dB)")
	ax.set_title(f"Total Harmonic Distortion: {thd_db:.2f} dBc")
	axis_top = np.ceil(psd_db.max() / 5.0) * 5.0
	ax.set_ylim(DB_FLOOR_DB, axis_top)
	ax.grid(True, linestyle=":")

	fund_entry = harmonic_data[0]
	fundamental_handle, = ax.plot(
		fund_entry["freq"] / 1000.0,
		fund_entry["power_db"],
		marker="o",
		color="tab:red",
		linestyle="None",
		label="Fundamental",
	)
	ax.annotate(
		"F\n{:.3f} kHz".format(fund_entry["freq"] / 1000.0),
		xy=(fund_entry["freq"] / 1000.0, fund_entry["power_db"]),
		xytext=(0, 10),
		textcoords="offset points",
		ha="center",
		color="tab:red",
		fontsize=9,
	)

	harmonics_handle = None
	for entry in harmonic_data[1:]:
		label = f"H{entry['order']}"
		handle = ax.plot(
			entry["freq"] / 1000.0,
			entry["power_db"],
			marker="o",
			color="tab:red",
			linestyle="None",
			label="Harmonics" if harmonics_handle is None else "_nolegend_",
		)[0]
		if harmonics_handle is None:
			harmonics_handle = handle
		ax.annotate(
			f"{label}\n{entry['freq'] / 1000.0:.3f} kHz",
			xy=(entry["freq"] / 1000.0, entry["power_db"]),
			xytext=(0, 10),
			textcoords="offset points",
			ha="center",
			color="tab:red",
			fontsize=9,
		)

	if have_harmonics and harmonics_handle is not None:
		ax.legend(
			[fundamental_handle, harmonics_handle, dc_noise_line],
			["Fundamental", "Harmonics", "DC and Noise"],
			loc="best",
		)
	else:
		ax.legend(
			[fundamental_handle, dc_noise_line],
			["Fundamental", "DC and Noise"],
			loc="best",
		)


def main() -> None:
	rng = np.random.default_rng(seed=0)

	# The power of a signal is the sum of the absolute square of its samples
	# divided by signal length, equivalent to the square of its RMS level.
	# Create a unit chirp in white Gaussian noise sampled at 1 kHz for 1.2 s.
	N = 1200
	Fs = 1000.0
	t = np.arange(N) / Fs
	sigma = 0.01
	s = chirp_signal(t, f0=100.0, t1=1.0, f1=300.0, method="linear") #+ sigma * rng.standard_normal(size=t.shape)

	# Verify that the RMS-based power estimate matches the bandpower integration.
	p_rms = rms(s) ** 2
	pow_bp = bandpower(s, Fs, (0.0, Fs / 2.0))
	print("Chirp power estimates:")
	print(f"  RMS power          : {p_rms:.6f}")
	print(f"  Bandpower [0,Fs/2] : {pow_bp:.6f}")

	# Use the occupied bandwidth computation to isolate the band that contains
	# 99% of the total power, and visualize the region on the spectrum plot.
	fig_obw, ax_obw = plt.subplots()
	obw_result = occupied_bandwidth(s, Fs, occupancy=0.99, plot=True, ax=ax_obw)
	print("\nOccupied bandwidth (99% power):")
	print(f"  Width  : {obw_result.width:.2f} Hz")
	print(f"  f_low  : {obw_result.f_low:.2f} Hz")
	print(f"  f_high : {obw_result.f_high:.2f} Hz")
	print(f"  Power  : {obw_result.power:.6f}")
	powtot = obw_result.power / 0.99
	print(f"  Total power est.  : {powtot:.6f}")

	# A nonlinear power amplifier yields a third-order distorted version of a
	# 60 Hz sinusoid. Sample the signal at 3.6 kHz for 2 seconds.
	Fs = 3600.0
	t = np.arange(0.0, 2.0, 1.0 / Fs)
	x = np.sin(2.0 * np.pi * 60.0 * t)
	y = np.polyval(np.ones(4), x) + rng.standard_normal(size=t.shape)

	# Visualize the spectrum, annotating the fundamental and harmonic components.
	fig_thd, ax_thd = plt.subplots()
	plot_thd(y, Fs, fundamental=60.0, harmonics=3, ax=ax_thd)

	# Use bandpower to quantify energy in each harmonic band and express the
	# result as percentages and decibels relative to the total power.
	pwr_tot = bandpower(y, Fs, (0.0, Fs / 2.0))
	print("\nHarmonic power distribution:")
	print(f"  Total power [0,Fs/2] : {pwr_tot:.6f}")

	harmonic_labels = ["Fundamental", "First", "Second"]
	harmonic_freqs = np.array([60.0, 120.0, 180.0])
	power = np.zeros_like(harmonic_freqs)
	for idx, freq in enumerate(harmonic_freqs):
		band = (freq - 10.0, freq + 10.0)
		band = (max(0.0, band[0]), min(Fs / 2.0, band[1]))
		power[idx] = bandpower(y, Fs, band)

	percent = power / pwr_tot * 100.0
	in_db = pow2db(power)

	print(f"\n{'Harmonic':<15}{'Freq (Hz)':>10}{'Power':>15}{'Percent (%)':>15}{'Power (dB)':>15}")
	for label, freq, pwr, pct, db in zip(harmonic_labels, harmonic_freqs, power, percent, in_db):
		print(f"{label:<15}{freq:>10.2f}{pwr:>15.6f}{pct:>15.2f}{db:>15.2f}")

	plt.tight_layout()
	plt.show()


if __name__ == "__main__":
	main()

