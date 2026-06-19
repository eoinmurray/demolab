"""Interactive LIF neuron — drag the sliders, watch the voltage trace and firing rate update."""
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


def simulate_lif(
    i_tonic: float,
    duration: float,
    dt: float,
    tau_m: float,
    v_rest: float,
    v_reset: float,
    v_thresh: float,
    r_m: float,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    n_steps = int(duration / dt)
    t = np.arange(n_steps) * dt
    v = np.empty(n_steps)
    spikes: list[float] = []
    v_curr = v_rest
    for i in range(n_steps):
        dv = (-(v_curr - v_rest) + r_m * i_tonic) / tau_m
        v_curr = v_curr + dv * dt
        if v_curr >= v_thresh:
            spikes.append(float(t[i]))
            v[i] = 0.0
            v_curr = v_reset
        else:
            v[i] = v_curr
    return t, v, spikes


st.set_page_config(page_title="LIF neuron", layout="wide")
st.title("Leaky integrate-and-fire neuron")
st.caption(
    "Drag any slider in the sidebar to update. Threshold crossings reset to V_reset and are drawn as upward spikes at 0 mV."
)

with st.sidebar:
    st.header("Parameters")

    st.subheader("Input")
    i_tonic = st.slider("Tonic current I (nA)", 0.0, 6.0, 2.5, 0.05)
    r_m = st.slider("Membrane resistance R_m (MΩ)", 1.0, 30.0, 10.0, 0.5)

    st.subheader("Membrane")
    tau_m = st.slider("Time constant τ_m (ms)", 1.0, 50.0, 10.0, 0.5)
    v_rest = st.slider("Resting potential V_rest (mV)", -90.0, -40.0, -65.0, 0.5)
    v_reset = st.slider("Reset potential V_reset (mV)", -90.0, -40.0, -70.0, 0.5)
    v_thresh = st.slider("Threshold V_thresh (mV)", -60.0, -20.0, -50.0, 0.5)

    st.subheader("Simulation")
    duration = st.slider("Duration (ms)", 20.0, 500.0, 100.0, 10.0)
    dt = st.slider("Timestep Δt (ms)", 0.01, 1.0, 0.1, 0.01)

t, v, spikes = simulate_lif(i_tonic, duration, dt, tau_m, v_rest, v_reset, v_thresh, r_m)
firing_rate_hz = 1000.0 * len(spikes) / duration if duration > 0 else 0.0
v_inf = v_rest + r_m * i_tonic
will_spike = v_inf >= v_thresh

m1, m2, m3 = st.columns(3)
m1.metric("Spikes", len(spikes))
m2.metric("Firing rate", f"{firing_rate_hz:.1f} Hz")
m3.metric(
    "Steady-state V∞",
    f"{v_inf:.1f} mV",
    delta="spiking" if will_spike else "subthreshold",
    delta_color="normal" if will_spike else "off",
)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(t, v, color="#1f77b4", linewidth=0.9)
ax.axhline(v_thresh, color="#cc4444", linestyle="--", linewidth=0.8, label="V_thresh")
ax.axhline(v_rest, color="#888", linestyle=":", linewidth=0.7, label="V_rest")
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Membrane potential (mV)")
ax.set_xlim(0, duration)
ax.set_ylim(min(v_reset, v_rest) - 5, 10)
ax.legend(loc="lower right", fontsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
st.pyplot(fig, clear_figure=True)

with st.expander("Equations"):
    st.markdown(
        r"""
Subthreshold dynamics:

$$\tau_m \frac{dV}{dt} = -(V - V_\text{rest}) + R_m\, I$$

Spike-and-reset rule:

$$V(t) \geq V_\text{thresh} \;\Longrightarrow\; \text{spike at } t,\quad V \leftarrow V_\text{reset}$$

Forward Euler integration:

$$V \leftarrow V + \frac{\Delta t}{\tau_m}\!\left[-(V - V_\text{rest}) + R_m\, I\right]$$

The neuron fires periodically when the steady-state voltage $V_\infty = V_\text{rest} + R_m I$ sits above $V_\text{thresh}$.
        """
    )
