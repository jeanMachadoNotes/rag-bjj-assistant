import "./App.css";

function Footer() {
    return (
        <div className="footer">
            <p>© {new Date().getFullYear()} | Built by <a href="https://jeanmachado.net" target="_blank" rel="noopener noreferrer">JM Creative</a></p>
        </div>
    );
}

export default Footer;