"use client";

import React from "react";
import { FaBars, FaTimes } from "react-icons/fa";

interface NavbarProps {
  onToggleMenu: () => void;
}

export default function Navbar({ onToggleMenu }: NavbarProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <nav className="absolute top-0 left-0 w-full flex items-center justify-between py-10 px-10">
      <h1 className="text-2xl font-extrabold text-emerald-800 underline underline-offset-8 decoration-orange-950">
        BarakoBama ☕🍃
      </h1>

      {/* Menu Toggle Button */}
      <button
        className="block lg:hidden p-2 text-amber-900 hover:text-amber-600"
        onClick={() => {
          setIsOpen(!isOpen);
          onToggleMenu(); // Call the parent's toggle function
        }}
      >
        {isOpen ? <FaTimes size={24} /> : <FaBars size={24} />}
      </button>

      {/* Navbar */}
      <div
        className={`fixed top-0 left-0 w-full h-full bg-zinc-50 dark:bg-zinc-900 transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "translate-x-full"
        } lg:translate-x-0 lg:relative lg:flex lg:items-center lg:justify-between lg:bg-transparent lg:p-0 lg:w-auto`}
      >
        <div className="flex flex-col lg:flex-row lg:space-x-4 lg:items-center lg:ml-auto lg:mt-0 mt-16">
          <a className="text-amber-900  hover:text-amber-600 rounded-lg px-4 py-2" href="/">
            Home
          </a>
          <a className="text-amber-900  hover:text-amber-600 rounded-lg px-4 py-2" href="/">
            Diseases
          </a>
          <a className="text-amber-900  hover:text-amber-600 rounded-lg px-4 py-2" href="/">
            About Us
          </a>
        </div>
        {/* Close Button */}
        <button
          className="lg:hidden absolute top-4 right-4 p-2 text-amber-900 hover:text-amber-600"
          onClick={() => {
            setIsOpen(false);
            onToggleMenu(); // Call the parent's toggle function
          }}
        >
          <FaTimes size={24} />
        </button>
      </div>
    </nav>
  );
}
