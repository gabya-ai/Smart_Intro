// Minimal Firebase client wrapper for the frontend React app
import { initializeApp } from 'firebase/app'
import {
  getAuth,
  setPersistence,
  browserLocalPersistence,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from 'firebase/auth'

// Keep same firebaseConfig used by the legacy public script
const firebaseConfig = {
  apiKey: 'AIzaSyC7UlBKRf-xIQg9A7zzhfoXyvot7a6t_qs',
  authDomain: 'genie-hi-front.firebaseapp.com',
  projectId: 'genie-hi-front',
  storageBucket: 'genie-hi-front.firebasestorage.app',
  messagingSenderId: '503651948869',
  appId: '1:503651948869:web:594bbbad692e192e8c462c',
}

const app = initializeApp(firebaseConfig)
const auth = getAuth(app)

// Persist across reloads (prevents flicker or relog loops)
// Note: setPersistence returns a promise
setPersistence(auth, browserLocalPersistence).catch(() => {})

export function observeAuth(cb) {
  return onAuthStateChanged(auth, cb)
}

export async function loginWithEmailPassword(email, password) {
  const { user } = await signInWithEmailAndPassword(auth, email, password)
  return user
}

export async function registerWithEmailPassword(email, password) {
  const { user } = await createUserWithEmailAndPassword(auth, email, password)
  return user
}

export async function getIdToken(user) {
  if (!user) return null
  return await user.getIdToken(true)
}
