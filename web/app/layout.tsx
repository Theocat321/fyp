export const metadata = {
  title: "VodaCare Support",
  description: "Mobile provider support chatbot",
};

import "../styles/globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <header className="app-header">
            <div className="brand-dot" />
            <div className="brand">
              <strong>VodaCare</strong> Support
            </div>
          </header>
          <main className="app-main">{children}</main>
        </div>
      </body>
    </html>
  );
}

