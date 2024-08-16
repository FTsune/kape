// Dropdown.tsx
import React, { useState, ReactNode } from "react";
import { FaChevronDown, FaChevronUp } from "react-icons/fa";
import { GiHamburgerMenu } from "react-icons/gi"; // Import hamburger icon

interface DropdownProps {
  icon: ReactNode; // Use ReactNode for the icon prop
}

const Dropdown: React.FC<DropdownProps> = ({ icon }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        className="flex items-center p-2 text-gray-800 dark:text-gray-200 hover:text-gray-600 dark:hover:text-gray-400"
        onClick={() => setIsOpen(!isOpen)}
      >
        {icon} {/* Display the icon prop */}
        {isOpen ? <FaChevronUp className="ml-2" /> : <FaChevronDown className="ml-2" />}
      </button>
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <a href="#step1" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">Step 1</a>
          <a href="#step2" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">Step 2</a>
          <a href="#step3" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">Step 3</a>
        </div>
      )}
    </div>
  );
};

export default Dropdown;
