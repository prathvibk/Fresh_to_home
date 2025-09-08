import React,{useEffect} from "react";

import AdminLogin from "./Components/AdminLogin";

const App = () => {
  useEffect(() => {
    document.title = "Salmon - Login";  // Set the title dynamically
  }, []); 
 
  return (
    <div>
      <AdminLogin />
    </div>
  );
};

export default App;









