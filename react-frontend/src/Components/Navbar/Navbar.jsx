import React from 'react'
import './Navbar.css'

const Navbar = () => {
  return (
    <div className='navbar'>
        <h1>AI Outdoor Camera</h1>
        <ul>
            <li>Home</li>
            <li>History</li>
            <li>Images</li>
            <li>Video</li>
        </ul>

        <div className='searchbox'>
            <input type="text" placeholder='Search'/>
            <img src="" alt="" />
        </div>

        <img src="" alt="" className='toggle-icon'/>

    </div>
  )
}

export default Navbar