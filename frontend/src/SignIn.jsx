import React, { useEffect, useState } from 'react'
import { observeAuth, loginWithEmailPassword, registerWithEmailPassword, getIdToken } from './firebaseInit'

function computeReturnUrl() {
  const params = new URLSearchParams(window.location.search)
  const fromQuery = params.get('return')
  if (fromQuery) return fromQuery
  const host = window.location.hostname
  const PROD_RETURN = 'https://genie-hi-503651948869.us-west1.run.app/'
  const LOCAL_RETURN = 'http://localhost:8501/home'
  if (host === 'localhost' || host.endsWith('.ngrok-free.app')) return LOCAL_RETURN
  return PROD_RETURN
}

export default function SignIn() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('')
  const [user, setUser] = useState(null)

  useEffect(() => {
    const unsub = observeAuth(async (u) => {
      setUser(u)
      if (u) {
        setStatus('Signed in — redirecting...')
        try {
          const token = await getIdToken(u)
          const target = new URL(computeReturnUrl())
          target.searchParams.set('id_token', token)
          window.location.href = target.toString()
        } catch (err) {
          console.error(err)
          setStatus('Could not complete sign-in.')
        }
      }
    })
    return () => unsub()
  }, [])

  async function onLogin(e) {
    e?.preventDefault()
    setStatus('Signing in...')
    try {
      await loginWithEmailPassword(email.trim(), password)
    } catch (err) {
      console.error(err)
      setStatus(err?.message || 'Sign-in failed.')
    }
  }

  async function onCreate(e) {
    e?.preventDefault()
    setStatus('Creating account...')
    try {
      await registerWithEmailPassword(email.trim(), password)
      setStatus('Account created! Now click “Sign in”.')
    } catch (err) {
      console.error(err)
      setStatus(err?.message || 'Registration failed.')
    }
  }

  return (
    <main style={{ maxWidth: 520, margin: '48px auto', padding: 24 }}>
      <h1>Sign in to Genie-Hi</h1>
      <p>Use your email and password to continue crafting cover letters in your own voice.</p>

      <label style={{ display: 'block', marginTop: 12 }}>Email</label>
      <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: '100%', padding: 10 }} placeholder="name@example.com" />

      <label style={{ display: 'block', marginTop: 12 }}>Password</label>
      <input value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: '100%', padding: 10 }} type="password" />

      <div style={{ display: 'grid', gap: 8, marginTop: 12 }}>
        <button onClick={onLogin} style={{ padding: 12, borderRadius: 8, background: '#5f2eea', color: '#fff' }}>Sign in</button>
        <button onClick={onCreate} style={{ padding: 12, borderRadius: 8, background: '#f0effb', color: '#5f2eea' }}>Create account</button>
      </div>

      <div id="status" role="status" style={{ marginTop: 16, color: '#666' }}>{status}</div>
    </main>
  )
}
