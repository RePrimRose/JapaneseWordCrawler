const express = require('express');
const Kuroshiro = require("kuroshiro").default;  // 수정 부분
const KuromojiAnalyzer = require("kuroshiro-analyzer-kuromoji");

const app = express();
const kuroshiro = new Kuroshiro();  // Kuroshiro 인스턴스 생성

app.use(express.json());

// Kuroshiro 초기화
kuroshiro.init(new KuromojiAnalyzer()).then(() => {
    console.log("Kuroshiro initialized");
});

app.post('/getFurigana', async (req, res) => {
    const { text } = req.body;
    try {
        const result = await kuroshiro.convert(text, { to: "hiragana", mode: "furigana" });
        console.log(result);
        res.send({ result });
    } catch (error) {
        console.error(error);
        res.status(500).send("Error processing furigana");
    }
});

app.listen(3000, () => {
    console.log("Kuroshiro API server running on port 3000");
});
