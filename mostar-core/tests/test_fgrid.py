from core.fgrid.models import Entity, Relationship
from core.fgrid.graph import fgrid_graph

def test_add_and_retrieve_entity():
    ent = Entity(
        id="test.node",
        type="TestNode",
        title="Test Node",
        tags=["unit-test"]
    )
    fgrid_graph.add_entity(ent)
    
    retrieved = fgrid_graph.get_entity("test.node")
    assert retrieved is not None
    assert retrieved.title == "Test Node"
    assert "unit-test" in retrieved.tags

def test_relationships_and_neighbors():
    node_a = Entity(id="node.a", type="Test", title="A")
    node_b = Entity(id="node.b", type="Test", title="B")
    fgrid_graph.add_entity(node_a)
    fgrid_graph.add_entity(node_b)
    
    rel = Relationship(
        source_id="node.a",
        target_id="node.b",
        relation_type="points_to"
    )
    fgrid_graph.add_relationship(rel)
    
    # Check relationship retrieval
    rels = fgrid_graph.get_relationships("node.a")
    assert len(rels) == 1
    assert rels[0].relation_type == "points_to"
    
    # Check neighbors
    neighbors = fgrid_graph.get_neighbors("node.a")
    assert len(neighbors) == 1
    assert neighbors[0][0].id == "node.b"
    assert neighbors[0][1] == "out:points_to"
    
    neighbors_in = fgrid_graph.get_neighbors("node.b")
    assert len(neighbors_in) == 1
    assert neighbors_in[0][0].id == "node.a"
    assert neighbors_in[0][1] == "in:points_to"
