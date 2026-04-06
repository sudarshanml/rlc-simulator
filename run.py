from sim import simulate, plot_waveforms
waveforms = simulate("examples/test.sp", duration=200e-12, timestep=1e-12)
fig = plot_waveforms(waveforms, title="RLC transient")

