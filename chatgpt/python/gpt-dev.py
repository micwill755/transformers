import urllib.request
import torch # we use PyTorch: https://pytorch.org
import torch.nn as nn
from torch.nn import functional as F
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


url = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"  # Replace with the actual URL
filename = "input.txt"

try:
    urllib.request.urlretrieve(url, filename)
    with open(filename, 'r') as file:
        text = file.read()
        #print("length of dataset in characters: ", len(text))
        # let's look at the first 1000 characters
        #print(text[:100])

        # here are all the unique characters that occur in this text
        chars = sorted(list(set(text)))
        vocab_size = len(chars)
        #print(''.join(chars))
        #print(vocab_size)

        # create a mapping from characters to integers
        stoi = { ch:i for i, ch in enumerate(chars) }
        itos = { i:ch for i, ch in enumerate(chars) }
        encode = lambda s: [stoi[c] for c in s] # encoder: take a string, output a list of integers
        decode = lambda l: ''.join([itos[i] for i in l]) if len(l) > 1 else ''.join([itos[l[0]]]) # decoder: take a list of integers, output a string
        
        #print(encode("hii there"))
        #print(decode(encode("hii there")))

        # let's now encode the entire text dataset and store it into a torch.Tensor
        data = torch.tensor(encode(text), dtype=torch.long)
        #print(data.shape, data.dtype)
        #print(data[:1000]) # the 1000 characters we looked at earier will to the GPT look like this

        # Let's now split up the data into train and validation sets
        n = int(0.9 * len(data)) # first 90% will be train, rest val
        train_data = data[:n]
        val_data = data[n:]

        #print(n, data.shape, train_data.shape, val_data.shape)
        #print(n, decode(val_data.numpy()))

        block_size = 8
        # in a chunk of 9 characters there is 8 examples
        train_data[:block_size + 1]

        x = train_data[:block_size]
        y = train_data[1:block_size+1]

        for t in range(block_size):
            context = x[:t+1]
            target = y[t]
            print(f"when input is {context} the target: {target}")
            '''d = decode(context.numpy())
            tar_char = target.item()
            print(f"when input is {d} the target: {itos[tar_char]}")'''

        torch.manual_seed(1337)
        batch_size = 4 # how many independent sequences will we process in parallel?
        block_size = 8 # what is the maximum context length for predictions?

        def get_batch(split):
            # generate a small batch of data of inputs x and targets y
            data = train_data if split == 'train' else val_data
            ix = torch.randint(len(data) - block_size, (batch_size,))
            x = torch.stack([data[i:i+block_size] for i in ix])
            y = torch.stack([data[i+1:i+block_size+1] for i in ix])
            return x, y

        xb, yb = get_batch('train')
        print('inputs:')
        print(xb.shape)
        print(xb)
        print('targets:')
        print(yb.shape)
        print(yb)

        print('----')

        for b in range(batch_size): # batch dimension
            for t in range(block_size): # time dimension
                context = xb[b, :t+1]
                target = yb[b,t]
                print(f"when input is {context.tolist()} the target: {target}")

        torch.manual_seed(1337)

    class BigramLanguageModel(nn.Module):

        def __init__(self, vocab_size):
            super().__init__()
            # each token directly reads off the logits for the next token from a lookup table
            self.token_embedding_table = nn.Embedding(vocab_size, vocab_size)

        def forward(self, idx, targets=None):

            # idx and targets are both (B,T) tensor of integers
            logits = self.token_embedding_table(idx) # (B,T,C)

            if targets is None:
                loss = None
            else:
                B, T, C = logits.shape
                logits = logits.view(B*T, C)
                targets = targets.view(B*T)
                loss = F.cross_entropy(logits, targets)

            return logits, loss

        def generate(self, idx, max_new_tokens):
            # idx is (B, T) array of indices in the current context
            for _ in range(max_new_tokens):
                # get the predictions
                logits, loss = self(idx)
                # focus only on the last time step
                logits = logits[:, -1, :] # becomes (B, C)
                # apply softmax to get probabilities
                probs = F.softmax(logits, dim=-1) # (B, C)
                # sample from the distribution
                idx_next = torch.multinomial(probs, num_samples=1) # (B, 1)
                # append sampled index to the running sequence
                idx = torch.cat((idx, idx_next), dim=1) # (B, T+1)
            return idx

    m = BigramLanguageModel(vocab_size)
    logits, loss = m(xb, yb)
    print(logits.shape)
    print(loss)

    print(decode(m.generate(idx = torch.zeros((1, 1), dtype=torch.long), max_new_tokens=100)[0].tolist()))

except Exception as e:
    print(f"An error occurred: {e}")

