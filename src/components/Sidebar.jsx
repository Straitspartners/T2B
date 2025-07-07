import { Link, useLocation } from "react-router-dom";

function Sidebar() {
  const { pathname } = useLocation();
  return (
    <div className="w-60 bg-gray-800 text-white min-h-screen p-4">
      <h1 className="text-xl font-bold mb-8">Tally2Books</h1>
      <nav className="flex flex-col space-y-4">
        <Link className={pathname === "/" ? "font-bold" : ""} to="/">Dashboard</Link>
        <Link className={pathname === "/masters" ? "font-bold" : ""} to="/masters">Masters</Link>
        <Link className={pathname === "/transactions" ? "font-bold" : ""} to="/transactions">Transactions</Link>
        <Link className={pathname === "/settings" ? "font-bold" : ""} to="/settings">Settings</Link>
      </nav>
    </div>
  );
}

export default Sidebar;
