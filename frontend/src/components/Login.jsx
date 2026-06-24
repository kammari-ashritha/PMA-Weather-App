import { GoogleLogin } from '@react-oauth/google'

export default function Login({ onLogin }) {
  return (
    <div className="login-page">
      <div className="bg-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>
      <div className="login-card">
        <h1 className="logo">Aurora Weather</h1>
        <p className="login-sub">by Kammari Ashritha · PM Accelerator</p>
        <div className="login-divider"></div>
        <h2 className="login-title">Sign in to continue</h2>
        <p className="login-desc">
          Save your weather searches, track forecasts,
          and export your data — all in one place.
        </p>
        <div className="google-btn-wrap">
          <GoogleLogin
            onSuccess={onLogin}
            onError={() => console.error('Login failed')}
            theme="filled_black"
            size="large"
            text="signin_with"
            shape="pill"
          />
        </div>
        <p className="login-note">
          Built for PM Accelerator AI Engineer Internship 2026
        </p>
      </div>
    </div>
  )
}