import tntorch as tn
import torch

def test_tensor():
    a = torch.rand(3, 3, 3)
    b = tn.Tensor(a, batch=True)

    for i in range(len(a)):
        c = tn.Tensor(a[i], batch=False)

        for j, core in enumerate(c.cores):
            assert torch.allclose(core, b.cores[j][i, ...])

        assert torch.allclose(c.torch(), b.torch()[i])