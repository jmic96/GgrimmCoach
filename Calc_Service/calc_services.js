import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { Generations, calculate, Move } from '@smogon/calc';

const app = express();
app.use(cors());
app.use(bodyParser.json({limit: '2mb'}));

const gens = new Generations(9);

app.post('/calc', (req, res) => {
  try {
    const g = gens.get(9);
    const { attacker, defender, move } = req.body;
    if (!attacker?.types?.length || !defender?.types?.length) {
      return res.status(400).json({ ok:false, error: "types required for attacker/defender" });
    }
    const result = calculate(g, attacker, defender, new Move(g, move));
    const range = result.range(); // [min,max] %
    res.json({ ok: true, range, desc: result.desc() });
  } catch(e) {
    res.status(400).json({ ok:false, error: String(e) });
  }
});

const PORT = 7070;
app.listen(PORT, () => console.log(`Calc service on http://localhost:${PORT}/calc`));
