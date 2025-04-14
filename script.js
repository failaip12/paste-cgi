const pasteTypeConstant = "pasteType";
const passwordFieldConstant = "passwordField";
const passwordTypeConstant = "password";
const plainTypeConstant = "plain";
const titleConstant = "title";
const expirationConstant = "expiration";
const plaintextConstant = "plaintext";
const pasteUrlConstant = "pasteUrl";
const pasteUrlSectionConstant = "pasteUrlSection";
const decryptedOutputConstant = "decryptedOutput";
const decryptButtonConstant = "decryptBtn";

let globalData;

function copyPaste() {
    const copyText = document.getElementById(
        document.getElementById(pasteUrlConstant)
            ? pasteUrlConstant
            : decryptedOutputConstant
    );
    copyText.select();
    copyText.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(copyText.value);
}

function togglePasteType() {
    const passwordType = document.getElementById(pasteTypeConstant)?.value || globalData?.type;
    const passwordField = document.getElementById(passwordFieldConstant);
    const decryptButton = document.getElementById(decryptButtonConstant);

    if (document.getElementById(titleConstant) && globalData?.title) {
        document.getElementById(titleConstant).textContent = "Title:" + globalData.title;
    }

    if (passwordType === passwordTypeConstant) {
        passwordField.style.display = "block";
        if (decryptButton) decryptButton.style.display = "block";
    } else {
        passwordField.style.display = "none";
        if (decryptButton) decryptButton.style.display = "none";
        if (document.getElementById(decryptedOutputConstant)) {
            document.getElementById(decryptedOutputConstant).textContent = globalData?.pasted_text || "";
        }
        document.getElementById(pasteUrlSectionConstant).style.display = "block";
    }
}

async function deriveKey(password, salt) {
    const encodedPassword = new TextEncoder().encode(password);
    const baseKey = await window.crypto.subtle.importKey(
        "raw",
        encodedPassword,
        { name: "PBKDF2" },
        false,
        ["deriveKey"]
    );

    const derivedKey = await window.crypto.subtle.deriveKey(
        {
            name: "PBKDF2",
            salt: salt,
            iterations: 600000,
            hash: "SHA-256",
        },
        baseKey,
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
    );

    return derivedKey;
}

async function encryptData(data, password) {
    const salt = window.crypto.getRandomValues(new Uint8Array(16));
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const key = await deriveKey(password, salt);
    const encodedData = new TextEncoder().encode(data);

    const encryptedContent = await window.crypto.subtle.encrypt(
        {
            name: "AES-GCM",
            iv: iv,
            tagLength: 128,
        },
        key,
        encodedData
    );

    const ciphertext = encryptedContent.slice(0, encryptedContent.byteLength - 16);
    const authTag = encryptedContent.slice(encryptedContent.byteLength - 16);

    return {
        ciphertext: new Uint8Array(ciphertext),
        iv: iv,
        authTag: new Uint8Array(authTag),
        salt: salt,
    };
}

async function decryptData(encryptedData, password) {
    const { ciphertext, iv, authTag, salt } = encryptedData;
    const key = await deriveKey(password, salt);

    const dataWithAuthTag = new Uint8Array(ciphertext.length + authTag.length);
    dataWithAuthTag.set(ciphertext, 0);
    dataWithAuthTag.set(authTag, ciphertext.length);

    const decryptedContent = await window.crypto.subtle.decrypt(
        { name: "AES-GCM", iv: iv, tagLength: 128 },
        key,
        dataWithAuthTag
    );

    return new TextDecoder().decode(decryptedContent);
}

async function handlePaste() {
    const type = document.getElementById(pasteTypeConstant).value;
    const title = document.getElementById(titleConstant).value;
    const expiration = document.getElementById(expirationConstant).value;
    const plaintext = document.getElementById(plaintextConstant).value;
    const password = document.getElementById(passwordTypeConstant).value;

    let pasted_text = "";

    if (type === plainTypeConstant) {
        if (!plaintext || !title) return alert("Enter title and paste.");
        pasted_text = plaintext;
    } else {
        if (!plaintext || !password || !title) return alert("Enter title, paste and password.");
        const encrypted = await encryptData(plaintext, password);
        pasted_text = btoa(JSON.stringify(encrypted));
    }

    const currentPath = window.location.origin;

    try {
        const response = await fetch(currentPath + "/submit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                type: type,
                title: title,
                expiration: expiration,
                pasted_text: pasted_text,
            }),
        });

        if (response.ok) {
            const jsonResponse = await response.json();
            document.getElementById(pasteUrlConstant).value = currentPath + "/get?id=" + jsonResponse.id;
            document.getElementById(pasteUrlSectionConstant).style.display = "block";
        } else {
            console.error("Failed to submit data. Status:", response.status);
        }
    } catch (error) {
        console.error("Error making the POST request:", error);
    }
}

async function handleDecrypt() {
    const base64 = globalData.pasted_text;
    const password = document.getElementById(passwordTypeConstant).value;
    if (!base64 || !password) return alert("Enter encrypted text and password.");

    try {
        const parsed = JSON.parse(atob(base64));
        const encryptedData = {
            salt: new Uint8Array(Object.values(parsed.salt)),
            iv: new Uint8Array(Object.values(parsed.iv)),
            authTag: new Uint8Array(Object.values(parsed.authTag)),
            ciphertext: new Uint8Array(Object.values(parsed.ciphertext)),
        };

        const decrypted = await decryptData(encryptedData, password);
        document.getElementById(decryptedOutputConstant).value = decrypted;
        document.getElementById(pasteUrlSectionConstant).style.display = "block";
    } catch (err) {
        document.getElementById(decryptedOutputConstant).value = "❌ Decryption failed.";
    }
}

async function loadPasteFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get("id");

    if (!id) return;

    const fetchUrl = `${window.location.origin}/paste?id=${id}`;

    try {
        const response = await fetch(fetchUrl);
        if (!response.ok) throw new Error("Failed to fetch data");

        globalData = await response.json();
        togglePasteType();
    } catch (error) {
        alert("No File Found");
        console.error("Error fetching data:", error);
    }
}

window.onload = async function () {
    let path = window.location.pathname;
    if (path != "/get")
        return;
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');

    const fetchUrl = `${window.location.origin}/paste?id=${id}`;

    try {
        const response = await fetch(fetchUrl);

        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }

        const data = await response.json();

        globalData = data;
        togglePasteType()
    } catch (error) {
        alert("No File Found")
        console.error('Error fetching data:', error);
    }
};