from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import logging
import re
from core.logging import InterceptHandler
from core.config import ENSEMBL_URL
from api.utils.metadata import (
    get_genome_id_from_assembly_accession_id,
    get_assembly_accession_from_ncbi,
)

logging.getLogger().handlers = [InterceptHandler()]

router = APIRouter()


# Resolve species home
# https://rapid.ensembl.org/Homo_sapiens_GCA_009914755.4/
# https://rapid.ensembl.org/Homo_sapiens_GCA_009914755.4/Info/Index
@router.get("/{species_url_name}/{subpath:path}", name="Rapid Species Home")
async def resolve_species(request: Request, species_url_name: str, subpath: str):
    if re.search("_GCA_|_GCF_", species_url_name):
        _, accession_id = re.split("_GCA_|_GCF_", species_url_name)
    else:
        logging.error("Genome url name missing GCA assembly accession id")
        raise HTTPException(
            status_code=400, detail="Genome url name missing GCA assembly accession id"
        )

    assembly_accession_id = "GCA_" + accession_id

    # RefSeqs have GCF prefix but version could be different. So fetch it from ncbi
    if assembly_accession_id.endswith("rs"):
        trimmed_assembly_accession_id = re.sub("rs$", "", assembly_accession_id)
        ncbi_dataset_report = get_assembly_accession_from_ncbi(
            trimmed_assembly_accession_id
        )

        if ncbi_dataset_report:
            assembly_accession_id = ncbi_dataset_report["paired_accession"]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Genome not found for accession {assembly_accession_id}",
            )

    genome_object = get_genome_id_from_assembly_accession_id(assembly_accession_id)

    if genome_object:
        genome_id = genome_object["genome_uuid"]
        genome_tag = genome_object["genome_tag"]
        if genome_tag:
            url = f"{ENSEMBL_URL}/species/{genome_tag}"
        else:
            url = f"{ENSEMBL_URL}/species/{genome_id}"
        return RedirectResponse(url)
    else:
        raise HTTPException(status_code=404, detail="Genome not found")


@router.get("/", name="Rapid Home")
async def resolve_home(request: Request):
    return RedirectResponse(ENSEMBL_URL)
