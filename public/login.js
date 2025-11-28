// Authentication state
let isAuthenticated = false;

// Check if user is already logged in (from localStorage)
function checkAuth() {
  const authToken = localStorage.getItem('authToken');
  const rememberMe = localStorage.getItem('rememberMe');
  
  // If user has auth token and rememberMe is checked, redirect to main app
  // (Only auto-redirect if they checked "Remember me")
  if (authToken && rememberMe === 'true') {
    // User is already logged in, redirect to main app
    window.location.href = '/';
    return;
  }
}

// Handle login form submission
function handleLogin(event) {
  event.preventDefault();
  
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const rememberMe = document.getElementById('rememberMe').checked;
  const loginError = document.getElementById('loginError');
  const loginBtn = document.getElementById('loginBtn');
  
  // Clear previous errors
  loginError.style.display = 'none';
  loginBtn.disabled = true;
  loginBtn.textContent = 'Signing in...';
  
  // Hardcoded credentials
  const HARDCODED_EMAIL = 'admin@minerva.com';
  const HARDCODED_PASSWORD = 'admin123';
  
  // Simulate login delay
  setTimeout(() => {
    // Validate against hardcoded credentials
    if (email === HARDCODED_EMAIL && password === HARDCODED_PASSWORD) {
      // Store auth token
      const authToken = 'auth_token_' + Date.now();
      localStorage.setItem('authToken', authToken);
      // Store rememberMe as string 'true' or 'false'
      localStorage.setItem('rememberMe', rememberMe ? 'true' : 'false');
      
      isAuthenticated = true;
      // Redirect to main app
      window.location.href = '/';
    } else {
      loginError.textContent = 'Invalid email or password';
      loginError.style.display = 'block';
      loginBtn.disabled = false;
      loginBtn.textContent = 'Sign In';
    }
  }, 1000);
}

// Handle signup button
function handleSignup() {
  alert('Sign up functionality coming soon!');
  // You can implement signup page/modal here
}

// Setup login event listeners
function setupLoginListeners() {
  const loginForm = document.getElementById('loginForm');
  const signupBtn = document.getElementById('signupBtn');
  
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
  
  if (signupBtn) {
    signupBtn.addEventListener('click', handleSignup);
  }
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupLoginListeners();
  });
} else {
  checkAuth();
  setupLoginListeners();
}

