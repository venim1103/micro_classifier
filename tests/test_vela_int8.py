import torch
import torch.nn.functional as F

from teacher.vela_int8 import HostEmbedding, Int8Linear, quantize_int8


def test_quantization_error_is_at_most_half_a_step():
    weight = torch.randn(16, 256).to(torch.bfloat16)
    values, scale = quantize_int8(weight, group_size=64)
    restored = values.view(16, 4, 64).float() * scale.float()[..., None]
    error = (restored - weight.float().view(16, 4, 64)).abs()
    assert values.dtype == torch.int8
    assert values.abs().max() <= 127
    assert torch.all(error <= 0.5001 * scale.float()[..., None])


def test_int8_linear_runs_a_bf16_matmul_close_to_the_original():
    torch.manual_seed(0)
    weight = torch.randn(32, 128)
    layer = Int8Linear(128, 32, group_size=32)
    layer.load(weight)
    inputs = torch.randn(3, 5, 128)
    output = layer(inputs)
    expected = F.linear(inputs, weight)
    assert output.dtype == torch.bfloat16
    assert torch.equal(output, F.linear(inputs.bfloat16(), layer.dequantized_weight()))
    assert (output.float() - expected).norm() / expected.norm() < 0.02
    layer.reference_weight = weight.bfloat16
    assert torch.equal(layer(inputs), F.linear(inputs.bfloat16(), weight.bfloat16()))


def test_host_embedding_is_not_moved_with_the_module():
    table = torch.randn(10, 4)
    embedding = HostEmbedding()
    embedding.weight_host = table
    embedding.to("meta")
    ids = torch.tensor([[1, 2], [3, 9]])
    assert list(embedding.parameters()) == []
    assert torch.equal(embedding(ids), table[ids])
