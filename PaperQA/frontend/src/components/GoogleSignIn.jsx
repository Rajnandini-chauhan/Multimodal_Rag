import { useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function GoogleSignIn({ onError }) {
  const { googleLogin } = useAuth();
  const navigate = useNavigate();
  const buttonRef = useRef(null);

  useEffect(() => {
    let isMounted = true;

    async function handleCredentialResponse(response) {
      if (!response || !response.credential) return;
      try {
        await googleLogin(response.credential);
        if (isMounted) navigate("/");
      } catch (err) {
        if (onError) {
          onError(
            err.response?.data?.detail || "Google authentication failed."
          );
        }
      }
    }

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

    function initGoogle() {
      if (window.google && buttonRef.current && clientId) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
        });
        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: "outline",
          size: "large",
          width: "100%",
        });
      }
    }

    if (window.google) {
      initGoogle();
    } else {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = () => {
        if (isMounted) initGoogle();
      };
      document.body.appendChild(script);
    }

    return () => {
      isMounted = false;
    };
  }, [googleLogin, navigate, onError]);

  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  if (!clientId) {
    return (
      <div className="text-center p-2 border border-pencil-light/50 rounded text-xs font-mono text-pencil">
        Google Sign-In ready (add VITE_GOOGLE_CLIENT_ID to .env)
      </div>
    );
  }

  return <div ref={buttonRef} className="w-full flex justify-center my-2" />;
}
