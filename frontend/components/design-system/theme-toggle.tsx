"use client";

export function ThemeToggle() {
  function toggle() {
    const next = document.documentElement.classList.contains("dark") ? "light" : "dark";
    document.documentElement.classList.toggle("dark", next === "dark");
    localStorage.setItem("kazilayer-theme", next);
  }
  return <button className="button-secondary" onClick={toggle}>Toggle theme</button>;
}
