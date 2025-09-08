import React, { useState } from "react";
import axios from "axios";
import { toast, ToastContainer } from "react-toastify";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import "react-toastify/dist/ReactToastify.css";

const LoginForm = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [hover, setHover] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const loginData = { email, password };
  
    try {
      const response = await axios.post("http://localhost:5000/admin_login", loginData, {
        headers: { "Content-Type": "application/json" },
        withCredentials: true, // Ensure cookies are sent with the request
      });
  
      if (response.status === 200) {
        toast.success("Login successful!");
        setTimeout(() => {
          window.location.href = "http://localhost:5000/admin_index";    
        }, 2000);
      }
    } catch (error) {
      if (error.response) {
        toast.error(error.response.data.message || "Invalid credentials!");
      } else if (error.request) {
        toast.error("No response from the server.");
      } else {
        toast.error("An error occurred while logging in.");
      }
    }
  };

  return (
    <div className="mainContainer">
      <style>
       {`
          .s_b_btn{
            margin-top: 20px;
          }

          button:hover {
            background-position: right center;
            text-decoration: none;
          }
       `}
      </style>
      <h1 style={styles.title}>SALMON FISH SELL POINT</h1>

      <div style={styles.formContainer}>
        <h2 style={styles.heading}>Admin Login</h2>
        <form onSubmit={handleSubmit}>
          <div style={styles.inputGroup}>
            <input
              type="email"
              id="username"
              name="email"
              value={email}
              placeholder="Enter Your Email"
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
            />
          </div>

          <div style={styles.inputGroup}>
            <div style={{ position: "relative" }}>
              <input
                type={passwordVisible ? "text" : "password"} // Toggle password visibility
                id="password"
                name="password"
                value={password}
                placeholder="Enter Your Password"
                onChange={(e) => setPassword(e.target.value)}
                required
                style={styles.input}
              />
              <FontAwesomeIcon
                icon={passwordVisible ? faEyeSlash : faEye} // Toggle icon based on visibility
                onClick={() => setPasswordVisible(!passwordVisible)}
                onMouseEnter={() => setHover(true)}
                onMouseLeave={() => setHover(false)}
                style={{ 
                  position: "absolute", 
                  right: "10px", 
                  top: "50%", 
                  transform: "translateY(-50%)", 
                  cursor: "pointer",
                  color: hover ? "#0056b3" : "#007bff",
                }}
              />
            </div>
          </div>

          <button type="submit" style={styles.button}>Login</button>
        </form>
        <a href="http://localhost:5000/seller_login">
          <button type="button" style={styles.button} className="s_b_btn">Seller Login</button>
        </a>

        <a href="http://localhost:5000/buyer_login">
          <button type="button" style={styles.button} className="s_b_btn">Buyer Login</button>
        </a>

      </div>
      <ToastContainer />
    </div>
  );
};



const styles = {
  mainContainer: {
    backgroundImage: "url('../public/background/bg1.jpg')",
    backgroundRepeat: "no-repeat",
    backgroundSize: "cover",
    backgroundPosition: "center center",
    textAlign: "center",
  },

  formContainer: {
    background: "white",
    padding: "20px",
    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
    borderRadius: "8px",
    width: "100%",
    maxWidth: "300px",
    margin: "0",
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    marginTop: "30px",
  },
  heading: {
    textAlign: "center",
  },
  inputGroup: {
    marginBottom: "20px",
  },
  input: {
    width: "100%",
    padding: "12px",
    fontSize: "16px",
    border: "1px solid #ccc",
    borderRadius: "4px",
    boxSizing: "border-box",
  },


  s_b_btn: {
    marginTop: "10px",
  },
  

  button: {
    width: "100%",
    padding: "10px",
    cursor: "pointer",

    backgroundImage: 'linear-gradient(to right, #83a4d4 0%, #b6fbff 51%, #83a4d4 100%)',
    textAlign: 'center',
    transition: '0.5s',
    backgroundSize: '200% auto',
    borderRadius: '5px',
    border: 'none',
    fontWeight: 'bold',
  },


  title: {
    fontSize: "40px",
    letterSpacing: "3px",
    color: "white",
    backgroundColor: "black",
    margin: "0",
    padding: "20px 40px",
    textAlign: "center",
  },
};

// npm install --save @fortawesome/react-fontawesome @fortawesome/free-solid-svg-icons

export default LoginForm;