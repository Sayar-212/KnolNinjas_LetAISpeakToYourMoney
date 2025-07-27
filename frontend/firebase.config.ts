import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';

// Your Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBwLIZjSE3bdPGPp-6qhYfcJTcmq2JWnFA",
  authDomain: "arthasashtri-419a9.firebaseapp.com",
  projectId: "arthasashtri-419a9",
  storageBucket: "arthasashtri-419a9.firebasestorage.app",
  messagingSenderId: "953558041281",
  appId: "1:953558041281:web:ea48a8d20cee767afa8a40",
  measurementId: "G-75T0Q3KYHY"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Auth functions
export const signInWithGoogle = () => signInWithPopup(auth, googleProvider);
export const signInWithEmail = (email: string, password: string) => signInWithEmailAndPassword(auth, email, password);
export const signUpWithEmail = (email: string, password: string) => createUserWithEmailAndPassword(auth, email, password);
export const logOut = () => signOut(auth);