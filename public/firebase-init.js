// public/firebase-init.js
// Firebase core + Auth setup (for hallowed-cortex-474405-b4)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.2/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  setPersistence,
  browserLocalPersistence
} from "https://www.gstatic.com/firebasejs/10.13.2/firebase-auth.js";

// --- Correct project configuration ---
const firebaseConfig = {
  apiKey: "AIzaSyAJwQFYlSwIJK-ijuZUTU1O56w6UxGOxCA",
  authDomain: "hallowed-cortex-474405-b4.firebaseapp.com",
  projectId: "hallowed-cortex-474405-b4",
};

// Initialize app + auth
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Persist login across tabs and reloads
await setPersistence(auth, browserLocalPersistence);

// --- Helper functions for index.html ---
export function observeAuth(callback) {
  return onAuthStateChanged(auth, callback);
}

export async function loginWithEmailPassword(email, password) {
  const { user } = await signInWithEmailAndPassword(auth, email, password);
  return user;
}

export async function registerWithEmailPassword(email, password) {
  const { user } = await createUserWithEmailAndPassword(auth, email, password);
  return user;
}

export async function logout() {
  await signOut(auth);
}
