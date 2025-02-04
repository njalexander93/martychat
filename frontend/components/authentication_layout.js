import Link from "next/link";

export default function AuthenticationForm({ children }) {
  return (
    <div className="h-screen bg-gradient-to-r from-gray-700 to-gray-300 flex items-center justify-center">
      <div className="flex flex-col items-center">
        {/* TODO: Add link to Martychat logo that takes user back to index */}
        <img src="/assets/MartyChat_Full-833x200.png" alt="MartyChat Logo" className="mb-6 w-1/2" />
        <div id="authentication-form" className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md auth-form-text">
            {children}
        </div>
      </div>
    </div>
  );
}
